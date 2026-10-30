"""One-off: run an India-targeted X pass using ONLY the Tier-2/3 city-booster queries.

Global 'my hometown' queries mostly surface non-Indian authors, so this pass searches
literal Indian Tier-2/3 city names for higher Indian yield. Usage: python3 -u run_india_pass.py
"""
import sys

import pipeline
import queries
import x_source

# Make the X source use booster-only queries for this run.
x_source.get_queries = lambda include_city_booster=False, limit=None: queries.city_booster_queries()

MAX_ITEMS = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

res = pipeline.run_pipeline(
    sources=("x",), max_items=MAX_ITEMS, lookback_days=10,
    enable_enrichment=True, progress=print,
)
print("\nTop Indian Tier-2/3 X leads:")
for l in res["x"][:15]:
    print(f"  [{l['final_score']}] {l['name'] or l['author_handle']} "
          f"({l['persona_tier']}/{l['persona']}) - {l['hometown']} - {l['post_url']}")
