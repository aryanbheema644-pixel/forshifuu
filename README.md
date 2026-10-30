# HomeTownTalks — Lead Discovery (X + LinkedIn)

Finds **founders / senior tech people / frontier-AI employees who are visiting their hometown and openly inviting local founders or the AI community to meet** — the signal behind Shifu Foundation's *HomeTownTalks*.

AI-powered social listening across **two sources**: it searches X and LinkedIn wide, lets an LLM judge the *meaning* of each post (not keywords), scores the lead against Shifu's ICP, and produces **two separate ranked priority lists** (plus a combined one). Comes with a Shifu-themed web UI.

Example signal (the post this was built around):
> "I'll be in my hometown Guntur sometime next week for few days. Anyone on my TL from there and are into AI research? I'd love to chat and offer any guidance."

## Pipeline

```
   LANE A — X                              LANE B — LinkedIn
   apidojo/tweet-scraper                   harvestapi/linkedin-post-search
   (tweet + author inline)                 (post + author profile inline)
        └──────────────┬─────────────────────────┘
                       ▼   tag each lead source = "x" | "linkedin"
          OpenRouter LLM — understand meaning, judge intent + persona (ICP)
                       ▼
          Score: intent_score (0–3) × persona_value (1–3) = final_score
                       ▼
          Cross-enrich: X leads → LinkedIn URL (profile-search-by-name)
                       ▼      (LinkedIn leads already carry their profile URL)
          Split by source → rank each
                       ▼
     x_leads.csv   +   linkedin_leads.csv   +   combined_leads.csv   +   latest.json (UI)
```

**Post → profile mapping:** both post-search actors return the author *inline* with the post, so there's no separate matching step within a network. The only cross-network match is finding a LinkedIn URL for an X-sourced lead (by name + company).

**Why keywords aren't the filter:** the signal has almost no fixed keywords, so queries only maximize *recall*; the LLM gives precision. Geography isn't hard-coded — Shifu targets every Indian district, so we match on "hometown / native place" language and let the LLM extract whichever town is named.

## Actors (verified live on Apify)

| Job | Actor | Notes |
|---|---|---|
| Find X posts | `apidojo/tweet-scraper` | keyword/boolean search, date window, author inline |
| Find LinkedIn posts | `harvestapi/linkedin-post-search` | keyword search, company/recency filters, author profile inline |
| X lead → LinkedIn URL | `harvestapi/linkedin-profile-search-by-name` | cross-network enrichment by name + company |

## Setup

Secrets live in `.env` (git-ignored). Copy `.env.example` → `.env` and fill in `APIFY_TOKEN` and `OPENROUTER_API_KEY`.
Deps (`requests`, `python-dotenv`) are already installed system-wide; otherwise `pip install -r requirements.txt`. The web UI uses only the Python standard library.

## Use the web UI (recommended)

```bash
python3 app.py
# then open http://localhost:8711
```

Pick sources (X / LinkedIn), lookback window, max items, model, and enrichment, then **Find leads**. Watch the live log, see stats, and browse the ranked **Combined / X / LinkedIn** tabs with clickable post + profile links. Filtered search is built in.

## Or run from the CLI

```bash
python3 pipeline.py                                   # both sources, config defaults
python3 pipeline.py --sources x                        # X only
python3 pipeline.py --sources linkedin                 # LinkedIn only
python3 pipeline.py --max-items 24 --queries-limit 4 --lookback-days 60 --no-linkedin-enrich   # cheap test
```

Flags: `--sources x,linkedin`, `--max-items`, `--lookback-days`, `--queries-limit N`, `--city-booster`, `--no-linkedin-enrich`, `--model`.

Outputs land in `outputs/`: `x_leads_<ts>.csv`, `linkedin_leads_<ts>.csv`, `combined_leads_<ts>.csv`, and `latest.json` (what the UI reads).

## Scoring (mirrors Shifu's ICP)

- **intent_score** (requires a hometown visit): explicit invite = 3, soft = 2, visit only = 1, no visit = 0.
- **persona**: founder / senior_tech = high (3), big_lab = medium (2), other = low (1).
- **final_score = intent_score × persona_value** (0–9). Qualified lead = `intent_score >= 2`. Only qualified X leads are LinkedIn-enriched (cost control).

## Files

| File | Role |
|---|---|
| `queries.py` | X + LinkedIn query sets |
| `x_source.py` / `linkedin_source.py` | fetch + normalize each source to a common lead schema |
| `classifier.py` | OpenRouter LLM intent/ICP judgment |
| `scoring.py` | deterministic scoring |
| `pipeline.py` | orchestrator (`run_pipeline()` + CLI) |
| `apify_runner.py` | thin Apify REST client |
| `app.py` + `web/index.html` | local web UI |
| `config.py` | all tunable knobs |

## Tuning (`config.py`)

`LOOKBACK_DAYS` (10), `MAX_TWEETS` (300, per-source cap), `OPENROUTER_MODEL` (`google/gemini-2.5-flash`; `-flash-lite` ≈ 8× cheaper), `MIN_INTENT_TO_QUALIFY` (2), `ENABLE_LINKEDIN_ENRICHMENT`, `MAX_ENRICH` (25), `LINKEDIN_PROFILE_MODE` (`Short`).

## Cost (approximate)

X search ~$0.25–0.40/1k tweets · LinkedIn post search ~$2/1k posts · LLM ~$0.12/300 posts (flash) · LinkedIn enrichment a few cents per qualified X lead.

## Known limits / next steps

- **Signal is genuinely rare** — expect a handful of leads per run; run often (e.g. daily) rather than expecting big batches.
- **LinkedIn ICP quality** depends on query tuning — the default LinkedIn queries are broad; add `authorsCompanies` filters (frontier labs) for precision.
- **Persona inference** from a short bio/headline is imperfect; broadened in the prompt, worth spot-checking the `persona` column.
- Possible additions: schedule it (cron/daily), push to a Google Sheet, de-dup across runs, India-geo filter on LinkedIn.
