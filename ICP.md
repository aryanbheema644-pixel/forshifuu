# HomeTownTalks — ICP (Ideal Customer Profile)

The person we want to surface and reach for Shifu Foundation's HomeTownTalks.

## Who (persona) — priority tiers
Mirrors Shifu's stated priorities; the LLM classifies each person into one.

| Tier | Persona | Who |
|---|---|---|
| **High** | `founder` | Founder / co-founder / entrepreneur / builder running their own startup |
| **High** | `senior_tech` | CTO, VP Eng, Eng Manager, staff / principal / senior engineer |
| **Medium** | `big_lab` | Works at a top tech co or frontier AI lab (Google, Microsoft, Meta, OpenAI, Anthropic, DeepMind, NVIDIA, xAI, Mistral, Cohere, World Labs…) but not clearly senior/founder |
| **Low** | `other` | Everyone else / unclear |

## Where (geography) — the hard gate
The person's **hometown / origin must be an Indian Tier-2 / Tier-3 city.** This is a strict filter.

- **Keep (`tier2_3`):** Guntur, Vijayawada, Visakhapatnam, Warangal, Coimbatore, Madurai, Indore, Nagpur, Jaipur, Lucknow, Kochi, Bhubaneswar… (73-city list in `keywords.md`)
- **Drop (`metro`):** Mumbai, Delhi/NCR, Bengaluru, Hyderabad, Chennai, Kolkata, Pune, Ahmedabad
- **Drop (`foreign`):** San Francisco, London, Singapore, anything outside India

## When (intent) — for the listening pipeline only
How ready-to-act the signal is. (In the people-first approach this becomes an outreach step instead.)

| Intent | Meaning | Score |
|---|---|---|
| `explicit` | Visiting hometown **and** openly inviting people to meet/chat | 3 |
| `soft` | Visiting hometown, hints at openness | 2 |
| visit only | Visiting, no openness shown | 1 |
| none | No hometown-visit signal | 0 |

## Scoring
`final_score = intent (0–3) × persona_value (High 3 / Medium 2 / Low 1)` → 0–9.
**Qualified lead = intent ≥ 2 AND hometown tier = tier2_3.**

## Fields extracted per lead
name · company · hometown · hometown_tier · persona · intent · source · post URL · post text · X profile · LinkedIn profile.

---

## How we determine if someone is from a Tier-2/3 city

This is the crux of the people-first approach. Current location is **not** reliable — a founder *lives* in Bengaluru or San Francisco but is *from* Guntur. So we infer **origin**, best signal first:

1. **Schooling (10th / 12th) — strongest.** If their LinkedIn Education lists a school, the school's city is almost certainly their hometown. Highest confidence.
2. **Undergraduate college location — strong proxy.** Most Indians do undergrad in or near their home state (regional/state-quota colleges). Undergrad in a Warangal/Guntur college → likely from there.
   - **Caveat:** national institutes (IIT / NIT / BITS / IIIT) draw students country-wide, so an IIT grad's campus ≠ hometown. For these, fall back to school or an explicit "from" statement.
3. **Explicit "from / born & raised" statements** in bio or posts ("proud Guntur boy", "born and raised in Warangal").
4. **Native language + regional cues** (languages listed, posts in Telugu/Tamil/Marathi, festival posts) — narrows to a region, not a city.
5. **Earliest location / first job** — early-career location is often near home.
6. **Name-based guessing** — unreliable; do **not** use as a primary signal.

**How to operationalize (LLM / Clay's Claygent):** feed each person's LinkedIn education + headline + early career + bio, and prompt:

> "Infer this person's hometown / origin city and whether it is an Indian Tier-2/3 city. Weigh schooling first, then undergrad location, then explicit 'from' statements. If their undergrad is a national institute (IIT/NIT/BITS/IIIT), do not use the campus city — rely on school or a stated hometown. Return: origin_city, tier (tier2_3 / metro / foreign / unknown), confidence, evidence."

**Honesty on accuracy:** no public signal is 100%. Education gives high confidence for a good share; the rest come back `unknown` and get **confirmed during outreach** ("where are you originally from?"). That's fine — the outreach message is cheap, and the question itself qualifies them.

---

## Two ways to use this ICP

- **Listening pipeline (built):** search X/LinkedIn posts → LLM applies this ICP → catches the rare *live* "visiting my hometown + let's meet" signal. A real-time trickle.
- **People-first (recommended, higher yield):** build a list of people matching **persona + Tier-2/3 origin** (ignore the live-intent step), reach out, and ask when they'll next be home. Far larger top-of-funnel; lower conversion but more leads in absolute terms.
