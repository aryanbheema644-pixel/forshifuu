"""Generate keywords.md (the keyword/query set) from queries.py — keeps docs in sync with code."""
import queries as q

FENCE = "```"
out = []
A = out.append
A("# HomeTownTalks — Keyword / Query Set\n")
A("These are the keywords and search queries the listening pipeline runs against X and LinkedIn.")
A("Keywords maximize *recall*; the OpenRouter LLM then judges meaning and filters to the ICP.\n")


def sec(title, items):
    A(f"## {title}  ({len(items)})\n")
    A(FENCE)
    out.extend(items)
    A(FENCE + "\n")


sec("Hometown / native-place terms", q.HOME_TERMS)
sec("Travel / arrival phrasings", q.TRAVEL_VERBS)
sec("Occasions (festivals + life events people travel home for)", q.OCCASIONS)
sec("Openness-to-meet (intent) markers", q.MEET_CORE)
sec("Audience / persona terms", q.AUD_CORE)
sec("Indian Tier-2/3 cities searched", q.TIER2_CITIES)

allq = q.get_queries()
A(f"## Full generated X query set  ({len(allq)} queries)\n")
A("Each line is one X advanced-search query (quoted phrases, OR groups).\n")
A(FENCE)
out.extend(f"{i:3d}. {s}" for i, s in enumerate(allq, 1))
A(FENCE + "\n")

liq = q.get_linkedin_queries()
A(f"## Full LinkedIn query set  ({len(liq)} queries)\n")
A(FENCE)
out.extend(f"{i:3d}. {s}" for i, s in enumerate(liq, 1))
A(FENCE)

with open("keywords.md", "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")
print(f"wrote keywords.md: {len(allq)} X queries, {len(liq)} LinkedIn queries")
