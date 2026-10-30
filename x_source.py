"""X (Twitter) source: run apidojo/tweet-scraper and normalize to the common lead schema."""
import datetime as dt

import apify_runner
import config
from queries import get_queries

SOURCE = "x"


def normalize(item: dict) -> dict:
    author = item.get("author") or {}
    handle = (author.get("userName") or author.get("username")
              or author.get("screen_name") or "")
    return {
        "source": SOURCE,
        "post_url": item.get("url") or item.get("twitterUrl") or "",
        "text": item.get("text") or item.get("fullText") or item.get("full_text") or "",
        "posted_at": item.get("createdAt") or item.get("created_at") or "",
        "author_handle": handle,
        "author_name": author.get("name") or "",
        "bio": author.get("description") or "",
        "location": author.get("location") or "",
        "followers": author.get("followers") or author.get("followersCount") or 0,
        "verified": bool(author.get("isVerified") or author.get("isBlueVerified")),
        "twitter_url": author.get("url") or (f"https://x.com/{handle}" if handle else ""),
        "linkedin_url": "",  # filled later by cross-network enrichment
        "query_matched": item.get("searchTerm") or "",
    }


def _build_input(actor: str, queries, max_items: int, since: str) -> dict:
    """Different X actors take different inputs; build the right one."""
    if "apidojo" in actor:
        inp = {"searchTerms": queries, "maxItems": max_items, "sort": config.SORT,
               "includeSearchTerms": True, "start": since}
        if config.TWEET_LANGUAGE:
            inp["tweetLanguage"] = config.TWEET_LANGUAGE
        return inp
    # jacquemus & similar: no server-side date filter
    return {"searchTerms": queries, "maxItems": max_items,
            "includeSearchTerms": True, "includeReplies": False}


def fetch(max_items: int, lookback_days: int, city_booster: bool = False,
          queries_limit=None, progress=print) -> list:
    actor = config.X_SEARCH_ACTOR
    queries = get_queries(include_city_booster=city_booster, limit=queries_limit)
    since = (dt.date.today() - dt.timedelta(days=lookback_days)).isoformat()
    run_input = _build_input(actor, queries, max_items, since)
    date_note = f"since {since}, " if "apidojo" in actor else ""
    progress(f"[X] searching {len(queries)} queries ({date_note}cap {max_items}) via {actor}...")
    raw = apify_runner.run_actor(actor, run_input, wait_secs=600)
    real = [i for i in raw if not i.get("noResults")]
    if raw and not real:
        progress("[X] ! actor returned only 'noResults' — likely X rate-limiting. "
                 "Wait a few minutes or switch X_SEARCH_ACTOR in config.py.")
    leads = [normalize(i) for i in real if (i.get("author") or i.get("text"))]
    progress(f"[X] {len(raw)} raw -> {len(leads)} normalized")
    return leads
