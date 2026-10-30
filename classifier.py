"""OpenRouter LLM classifier: turn a raw tweet into a structured HomeTownTalks judgment.

This is where 'understand the meaning, not the keywords' happens. The LLM returns
only semantic judgments + extracted fields; numeric scoring is done in Python
(scoring.py) so it stays deterministic and cheap to tune.
"""
import json

import requests

import config

SYSTEM_PROMPT = """You are a lead-qualification analyst for Shifu Foundation's "HomeTownTalks".

HomeTownTalks finds founders / senior tech people / frontier-AI employees who are
VISITING THEIR HOMETOWN (or native place) and are OPEN TO MEETING local founders
or the local AI/tech community, so Shifu can connect them.

You are given one social post (and the author's bio/location). Decide whether it
is this kind of lead and extract fields. Judge MEANING, not keywords.

Return ONLY a JSON object with these exact keys:
{
  "hometown_visit": true|false,   // author announces an upcoming or current trip to THEIR OWN hometown/native place/home city
  "openness": "explicit"|"soft"|"none",  // explicit = clearly invites people to meet/chat/connect; soft = hints at it; none = no invite
  "persona": "founder"|"senior_tech"|"big_lab"|"other",
      // founder    = founder/co-founder/entrepreneur/builder running their own startup
      // senior_tech= CTO, VP Eng, eng manager, staff/principal/senior engineer
      // big_lab    = works at a top tech/AI company OR any frontier AI lab/startup (Google, Microsoft, Meta, OpenAI,
      //              Anthropic, DeepMind, NVIDIA, xAI, Mistral, Cohere, Perplexity, Scale AI, World Labs, SSI, etc.)
      //              but not clearly senior/founder. A bio mentioning AI/ML research at a named lab counts here.
      // other      = none of the above, or identity unclear
  "name": "",      // author's best-guess full name ("" if unknown)
  "company": "",   // current company/org if inferable ("" if unknown)
  "hometown": "",  // the town/city/district they are visiting ("" if not stated)
  "hometown_tier": "tier2_3"|"metro"|"foreign"|"unknown",
      // tier2_3 = an INDIAN town/city that is NOT a top metro -> THIS is what we want. Examples: Guntur,
      //           Vijayawada, Visakhapatnam, Warangal, Nellore, Tirupati, Coimbatore, Madurai, Kochi, Mysuru,
      //           Hubli, Indore, Bhopal, Nagpur, Nashik, Surat, Rajkot, Jaipur, Jodhpur, Lucknow, Kanpur, Patna,
      //           Ranchi, Bhubaneswar, Raipur, Dehradun, Guwahati, Vijayawada, Trichy, Mangalore, Vadodara ...
      // metro   = a top Indian metro (Mumbai, Delhi/NCR incl. Gurgaon/Noida, Bengaluru, Hyderabad, Chennai, Kolkata, Pune, Ahmedabad)
      // foreign = any city OUTSIDE India (San Francisco, Melbourne, London, New York, Dubai, Singapore, Toronto ...)
      // unknown = hometown not stated or you cannot determine it
  "reason": ""     // <= 20 words, why this is or isn't a lead; use they/them, never guess gender from a name
}

Classify hometown_tier from the TOWN THEY ARE VISITING, not where they currently live. A frontier-lab
engineer living in San Francisco but visiting their hometown Guntur is tier2_3 (Guntur), not foreign.

hometown_visit is TRUE whenever the author is (or will soon be) in the place they are
FROM — even if they never use the word "hometown". Count indirect phrasings: "home for
Diwali", "back in Vijayawada next week", "heading to my native place", "landing in
Coimbatore to see family", "going home for the holidays", "back in my city". It is FALSE
for a generic post, or travel to a city they are NOT from (a conference or work trip).
Output JSON only, no prose."""

FEWSHOT_USER = """POST: "I'll be in my hometown Guntur sometime next week for a few days. Anyone on my TL from there and are into AI research? I'd love to chat and offer any guidance. (Appreciate retweets to reach some right folks!)"
AUTHOR_NAME: Gowthami
AUTHOR_BIO: Research @ a frontier AI lab. ML, LLMs.
AUTHOR_LOCATION: San Francisco"""

FEWSHOT_ASSISTANT = json.dumps({
    "hometown_visit": True,
    "openness": "explicit",
    "persona": "big_lab",
    "name": "Gowthami",
    "company": "frontier AI lab",
    "hometown": "Guntur",
    "hometown_tier": "tier2_3",
    "reason": "Frontier-lab researcher visiting hometown Guntur, explicitly inviting local AI folks to chat.",
})


def classify(tweet: dict) -> dict:
    """tweet = normalized dict with text, author_name, bio, location. Returns judgment dict."""
    user_msg = (
        f'POST: "{tweet.get("text", "")}"\n'
        f'AUTHOR_NAME: {tweet.get("author_name", "")}\n'
        f'AUTHOR_BIO: {tweet.get("bio", "")}\n'
        f'AUTHOR_LOCATION: {tweet.get("location", "")}'
    )
    payload = {
        "model": config.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": FEWSHOT_USER},
            {"role": "assistant", "content": FEWSHOT_ASSISTANT},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://shifu.foundation",
        "X-Title": "HomeTownTalks Lead Discovery",
    }
    try:
        r = requests.post(config.OPENROUTER_URL, headers=headers, json=payload, timeout=config.LLM_TIMEOUT)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
    except Exception as e:  # noqa: BLE001 - never let one bad tweet kill the run
        return _empty(f"error: {e}")
    return _normalize_judgment(data)


def _empty(reason: str) -> dict:
    return {
        "hometown_visit": False, "openness": "none", "persona": "other",
        "name": "", "company": "", "hometown": "", "hometown_tier": "unknown", "reason": reason,
    }


def _normalize_judgment(d: dict) -> dict:
    out = _empty("")
    out["hometown_visit"] = bool(d.get("hometown_visit"))
    openness = str(d.get("openness", "none")).lower()
    out["openness"] = openness if openness in ("explicit", "soft", "none") else "none"
    persona = str(d.get("persona", "other")).lower()
    out["persona"] = persona if persona in ("founder", "senior_tech", "big_lab", "other") else "other"
    tier = str(d.get("hometown_tier", "unknown")).lower()
    out["hometown_tier"] = tier if tier in ("tier2_3", "metro", "foreign", "unknown") else "unknown"
    for k in ("name", "company", "hometown", "reason"):
        out[k] = str(d.get(k, "") or "").strip()
    return out
