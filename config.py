"""Central configuration for the HomeTownTalks lead-discovery pipeline.

Secrets are read from the local .env file (never hard-coded here).
Everything else is a tunable knob you can safely change.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

# --- Secrets (from .env) ---
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# --- Apify actors (verified live on the Apify API) ---
# jacquemus: reliable, separate credential pool, 100% success claim, but NO server-side date filter.
# apidojo:   supports start-date / geo / language filters, but shares a pool that can rate-limit under heavy use
#            (returns only {"noResults": true} when throttled). Swap here if one is throttled.
X_SEARCH_ACTOR = "jacquemus~x-tweet-scraper"          # X / Twitter keyword search + author data
LINKEDIN_ACTOR = "harvestapi~linkedin-profile-search-by-name"  # name -> LinkedIn profile URL

# --- X search settings ---
LOOKBACK_DAYS = 10          # only pull tweets from the last N days (the signal is time-sensitive)
MAX_TWEETS = 300            # hard cap on tweets pulled per run (cost control)
TWEET_LANGUAGE = "en"       # "" to disable the language filter
SORT = "Latest"             # "Latest" or "Top"

# --- LLM classifier (OpenRouter) ---
OPENROUTER_MODEL = "google/gemini-2.5-flash"   # strong at nuanced JSON; use "google/gemini-2.5-flash-lite" for ~8x cheaper
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_MAX_WORKERS = 6         # parallel classification requests
LLM_TIMEOUT = 60

# --- Scoring / gating ---
MIN_INTENT_TO_QUALIFY = 2   # intent_score >= this => qualified lead (visit + some openness)
# Geographic ICP gate: the hometown they're visiting must be one of these tiers.
# Shifu targets Indian Tier-2/Tier-3 cities, so SF/Melbourne (foreign) and big metros are excluded.
# Add "metro" to also include top Indian metros; add "unknown" to keep leads whose city is unclear.
ALLOWED_HOMETOWN_TIERS = ("tier2_3",)
ENABLE_LINKEDIN_ENRICHMENT = True
MAX_ENRICH = 25             # cap LinkedIn lookups per run (cost control)
LINKEDIN_PROFILE_MODE = "Short"   # "Short" | "Full" | "Full + email search"

# --- Output ---
OUTPUT_DIR = ROOT / "outputs"
