"""HomeTownTalks dual-source lead-discovery pipeline (X + LinkedIn).

Flow per source:
  X        -> apidojo/tweet-scraper          (tweet + author inline)
  LinkedIn -> harvestapi/linkedin-post-search (post + author profile inline)
Then shared: OpenRouter LLM intent/ICP classify -> score -> cross-network LinkedIn
enrich (X leads only) -> split into per-source ranked lists -> CSVs + latest.json.

CLI:
  python3 pipeline.py                         # both sources, config defaults
  python3 pipeline.py --sources x             # X only
  python3 pipeline.py --max-items 20 --no-linkedin-enrich --queries-limit 3   # cheap test
"""
import argparse
import csv
import datetime as dt
import json
import re
from concurrent.futures import ThreadPoolExecutor

import apify_runner
import classifier
import config
import linkedin_source
import scoring
import x_source

CSV_COLUMNS = [
    "rank", "source", "final_score", "intent_score", "persona_tier", "persona", "openness",
    "name", "company", "hometown", "hometown_tier", "author_handle", "twitter_url", "linkedin_url",
    "post_url", "followers", "verified", "posted_at", "bio", "text", "reason", "query_matched",
]


# --------------------------- helpers ---------------------------
def dedup(leads: list) -> list:
    """One lead per (source, author); first seen wins (actors return newest first)."""
    seen, out = set(), []
    for t in leads:
        key = (t["source"], (t["author_handle"] or t["post_url"]).lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out


def classify_all(leads: list, progress=print) -> list:
    progress(f"[LLM] classifying {len(leads)} posts with {config.OPENROUTER_MODEL}...")
    with ThreadPoolExecutor(max_workers=config.LLM_MAX_WORKERS) as pool:
        judgments = list(pool.map(classifier.classify, leads))
    return [{**t, **j, **scoring.score(j)} for t, j in zip(leads, judgments)]


_LINKEDIN_RE = re.compile(r"https?://[\w.]*linkedin\.com/in/[\w\-%]+", re.I)


def _find_linkedin_url(item: dict) -> str:
    for v in item.values():
        if isinstance(v, str):
            m = _LINKEDIN_RE.search(v)
            if m:
                return m.group(0)
    for k in ("linkedinUrl", "profileUrl", "url", "publicProfileUrl"):
        v = item.get(k)
        if isinstance(v, str) and "linkedin.com/in/" in v.lower():
            return v
    return ""


def enrich_linkedin(leads: list, progress=print) -> None:
    """Cross-network: find a LinkedIn URL for qualified X leads (LinkedIn leads already have one)."""
    if not config.ENABLE_LINKEDIN_ENRICHMENT:
        progress("[enrich] LinkedIn enrichment disabled.")
        return
    targets = [l for l in leads if l["source"] == "x" and not l.get("linkedin_url")][: config.MAX_ENRICH]
    progress(f"[enrich] looking up LinkedIn for {len(targets)} X leads...")
    for lead in targets:
        name = (lead.get("name") or lead.get("author_name") or "").strip()
        if not name:
            continue
        parts = name.split()
        run_input = {
            "profileScraperMode": config.LINKEDIN_PROFILE_MODE,
            "firstName": parts[0],
            "lastName": parts[-1] if len(parts) > 1 else "",
            "maxItems": 1,
        }
        if lead.get("company"):
            run_input["currentCompanies"] = [lead["company"]]
        try:
            res = apify_runner.run_actor(config.LINKEDIN_ACTOR, run_input, wait_secs=180)
            lead["linkedin_url"] = _find_linkedin_url(res[0]) if res else ""
        except Exception as e:  # noqa: BLE001
            progress(f"[enrich] ! {name}: {e}")


def _rank(leads: list) -> list:
    def _fol(r):
        v = r.get("followers", 0)
        return int(v) if isinstance(v, (int, float)) else 0
    # sort only; rank is assigned per-list at write time (leads are shared across lists)
    return sorted(leads, key=lambda r: (r["final_score"], r["intent_score"], _fol(r)), reverse=True)


def _write_csv(leads: list, name: str) -> str:
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    path = config.OUTPUT_DIR / name
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        w.writeheader()
        for i, lead in enumerate(leads, 1):
            w.writerow({**lead, "rank": i})
    return str(path)


# --------------------------- main entry ---------------------------
def run_pipeline(sources=("x", "linkedin"), max_items=None, lookback_days=None,
                 queries_limit=None, city_booster=True, enable_enrichment=None,
                 model=None, progress=print) -> dict:
    """Run the pipeline and return {'x': [...], 'linkedin': [...], 'combined': [...], 'stats': {...}}."""
    max_items = max_items or config.MAX_TWEETS
    lookback_days = lookback_days if lookback_days is not None else config.LOOKBACK_DAYS
    if model:
        config.OPENROUTER_MODEL = model
    if enable_enrichment is not None:
        config.ENABLE_LINKEDIN_ENRICHMENT = enable_enrichment

    raw_leads = []
    if "x" in sources:
        raw_leads += x_source.fetch(max_items, lookback_days, city_booster, queries_limit, progress)
    if "linkedin" in sources:
        raw_leads += linkedin_source.fetch(max_items, lookback_days, queries_limit, progress)

    raw_leads = dedup(raw_leads)
    if not raw_leads:
        progress("No posts returned. Widen the lookback window or queries.")
        return {"x": [], "linkedin": [], "combined": [], "review": [],
                "stats": {"raw": 0, "qualified": 0, "review": 0}}

    scored = classify_all(raw_leads, progress)
    intent_ok = [r for r in scored if r["intent_score"] >= config.MIN_INTENT_TO_QUALIFY]
    qualified = [r for r in intent_ok if r.get("hometown_tier") in config.ALLOWED_HOMETOWN_TIERS]
    dropped = len(intent_ok) - len(qualified)
    progress(f"[score] {len(qualified)} qualified of {len(scored)} "
             f"(intent>={config.MIN_INTENT_TO_QUALIFY}, hometown tier in {config.ALLOWED_HOMETOWN_TIERS}; "
             f"{dropped} dropped for non-Tier-2/3 hometown)")

    # Broader REVIEW list: any Indian Tier-2/3 hometown visitor, regardless of openness strength
    # or persona (includes the strict-qualified ones). For manual eyeballing.
    review = _rank([r for r in scored if r.get("hometown_visit") and r.get("hometown_tier") == "tier2_3"])

    enrich_linkedin(qualified, progress)

    x_leads = _rank([l for l in qualified if l["source"] == "x"])
    li_leads = _rank([l for l in qualified if l["source"] == "linkedin"])
    combined = _rank(list(qualified))

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = {}
    if x_leads:
        paths["x"] = _write_csv(x_leads, f"x_leads_{ts}.csv")
    if li_leads:
        paths["linkedin"] = _write_csv(li_leads, f"linkedin_leads_{ts}.csv")
    if combined:
        paths["combined"] = _write_csv(combined, f"combined_leads_{ts}.csv")
    if review:
        paths["review"] = _write_csv(review, f"review_leads_{ts}.csv")

    result = {
        "x": x_leads, "linkedin": li_leads, "combined": combined, "review": review,
        "stats": {"raw": len(raw_leads), "qualified": len(qualified), "review": len(review),
                  "x": len(x_leads), "linkedin": len(li_leads),
                  "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
                  "sources": list(sources), "lookback_days": lookback_days, "paths": paths},
    }
    # latest.json for the UI
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    with open(config.OUTPUT_DIR / "latest.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    progress(f"[done] X: {len(x_leads)} | LinkedIn: {len(li_leads)} | combined: {len(combined)}")
    return result


def main():
    ap = argparse.ArgumentParser(description="HomeTownTalks dual-source lead discovery")
    ap.add_argument("--sources", default="x,linkedin", help="comma list: x,linkedin")
    ap.add_argument("--max-items", type=int, default=config.MAX_TWEETS)
    ap.add_argument("--lookback-days", type=int, default=config.LOOKBACK_DAYS)
    ap.add_argument("--queries-limit", type=int, default=None)
    ap.add_argument("--no-city-booster", action="store_true", help="skip the Tier-2/3 city sweep (faster/cheaper)")
    ap.add_argument("--no-linkedin-enrich", action="store_true", help="skip cross-network LinkedIn lookup")
    ap.add_argument("--model", default=None)
    args = ap.parse_args()

    res = run_pipeline(
        sources=tuple(s.strip() for s in args.sources.split(",") if s.strip()),
        max_items=args.max_items, lookback_days=args.lookback_days,
        queries_limit=args.queries_limit, city_booster=not args.no_city_booster,
        enable_enrichment=not args.no_linkedin_enrich, model=args.model,
    )
    for label in ("x", "linkedin"):
        leads = res[label]
        print(f"\nTop {label.upper()} leads:")
        for l in leads[:5]:
            print(f"  [{l['final_score']}] {l['name'] or l['author_handle']} "
                  f"({l['persona_tier']}/{l['persona']}) - {l['hometown']} - {l['post_url']}")


if __name__ == "__main__":
    main()
