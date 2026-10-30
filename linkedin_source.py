"""LinkedIn source: run harvestapi/linkedin-post-search and normalize to the common lead schema.

The post actor returns the author's profile inline (name, headline, profile URL),
so there is no separate post->profile mapping step and no cross-network enrichment
needed for LinkedIn leads (we already have their LinkedIn URL).
"""
import apify_runner
import config
from queries import get_linkedin_queries

SOURCE = "linkedin"

LINKEDIN_POST_ACTOR = "harvestapi~linkedin-post-search"

# lookback_days -> actor's postedLimit bucket
_POSTED_BUCKETS = [(1, "24h"), (7, "week"), (31, "month"), (93, "3months"),
                   (186, "6months"), (366, "year")]


def _posted_limit(lookback_days: int) -> str:
    for days, label in _POSTED_BUCKETS:
        if lookback_days <= days:
            return label
    return "any"


def _clean_url(url: str) -> str:
    return (url or "").split("?")[0]


def _as_int(v) -> int:
    if isinstance(v, bool):
        return 0
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, dict):
        for k in ("count", "total", "value", "reactions"):
            if isinstance(v.get(k), (int, float)):
                return int(v[k])
    return 0


def normalize(item: dict) -> dict:
    author = item.get("author") or {}
    return {
        "source": SOURCE,
        "post_url": item.get("linkedinUrl") or item.get("shareLinkedinUrl") or "",
        "text": item.get("content") or "",
        "posted_at": item.get("postedAt", {}).get("date") if isinstance(item.get("postedAt"), dict)
        else (item.get("postedAt") or ""),
        "author_handle": author.get("publicIdentifier") or "",
        "author_name": author.get("name") or "",
        "bio": author.get("info") or "",          # LinkedIn headline = strong ICP signal
        "location": author.get("location") or "",
        "followers": _as_int((item.get("engagement") or {}).get("reactions")),
        "verified": False,
        "twitter_url": "",
        "linkedin_url": _clean_url(author.get("linkedinUrl")),  # already known for LinkedIn leads
        "query_matched": item.get("query") or "",
    }


def fetch(max_items: int, lookback_days: int, queries_limit=None, progress=print) -> list:
    queries = get_linkedin_queries(limit=queries_limit)
    posted = _posted_limit(lookback_days)
    per_query = max(1, max_items // max(1, len(queries)))
    run_input = {
        "searchQueries": queries,
        "maxPosts": per_query,
        "postedLimit": posted,
        "sortBy": "date",
        "profileScraperMode": "short",
    }
    progress(f"[LinkedIn] searching {len(queries)} queries, posted<= {posted}, ~{per_query}/query...")
    raw = apify_runner.run_actor(LINKEDIN_POST_ACTOR, run_input, wait_secs=600)
    leads = [normalize(i) for i in raw if (i.get("author") or i.get("content"))]
    progress(f"[LinkedIn] {len(raw)} raw posts -> {len(leads)} normalized")
    return leads
