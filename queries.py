"""Search queries for the HomeTownTalks signal — WIDE language, India-anchored.

The signal: someone (founder / senior tech / frontier-AI) VISITING THEIR HOMETOWN
and OPEN TO MEETING local founders or the AI community.

People express "visiting my hometown" in dozens of ways — literal ("my hometown"),
Indian-English ("my native", "native place"), transliterated ("my ooru", "my gaon",
"my pind"), occasion-driven ("home for Diwali", "cousin's wedding", "summer break"),
or arrival-style ("landing in Guntur", "back in Warangal next week"). So the keyword
net is deliberately huge for RECALL. Precision comes from the LLM + the Tier-2/3 gate.

India-anchored three ways so the wide net doesn't drown in non-Indian posts:
  1. Indian-English / transliterated home words
  2. literal Indian Tier-2/3 city names (city sweep)
  3. Indian festivals & life events people travel home for.
"""

# --- Ways people say "my hometown" (literal + Indian-English + transliterated) ---
HOME_TERMS = [
    '"my hometown"', '"home town"', '"my hometown is"', '"from my hometown"',
    '"native place"', '"my native"', '"my native is"', '"native town"', '"native city"',
    '"my village"', '"my ooru"', '"my gaon"', '"my gaanv"', '"my pind"', '"my desh"',
    '"my roots"', '"back to my roots"', '"my birthplace"', '"where I was born"',
    '"where I grew up"', '"childhood town"', '"back home"', '"heading home"', '"going home"',
    '"coming home"', '"return home"', '"home for"', '"home this week"', '"visiting family"',
    '"back in my"', '"working from my hometown"', '"wfh from home"',
]

# --- Arrival / travel phrasings (paired with a city in the sweep) ---
TRAVEL_VERBS = [
    '"will be in"', '"i\'ll be in"', '"i will be in"', 'visiting', '"coming to"',
    '"landing in"', '"just landed in"', '"flying to"', '"heading to"', '"reached"',
    '"reaching"', '"back in"', '"in town"', '"road trip to"', '"train to"', '"few days in"',
    '"weekend in"', '"staying in"', '"spending the week in"',
]

# --- Occasions people travel home for (festivals + life events; India-biased) ---
OCCASIONS = [
    'Diwali', 'Deepavali', 'Sankranti', '"Makar Sankranti"', 'Pongal', 'Ugadi', 'Onam',
    'Dussehra', 'Dasara', 'Navratri', 'Navaratri', 'Holi', '"Durga Puja"', 'Bihu', 'Lohri',
    'Baisakhi', '"Ganesh Chaturthi"', '"Raksha Bandhan"', 'Vishu', '"Gudi Padwa"', 'Chhath',
    'Eid', 'Bakrid', 'Gurpurab', 'Christmas', '"New Year"', '"for the holidays"',
    '"for vacation"', '"summer break"', '"winter break"', '"family wedding"',
    '"family function"', '"cousin\'s wedding"', 'sabbatical', '"year-end break"',
]

# --- Openness-to-meet markers (core intent) ---
MEET_CORE = [
    '"happy to chat"', '"love to chat"', '"happy to meet"', '"love to meet"',
    '"love to connect"', '"happy to connect"', '"let\'s connect"', '"catch up"',
    '"offer guidance"', '"happy to help"', 'mentor', '"mentor students"', '"anyone from"',
    '"anyone around"', '"anyone in"', '"anyone here"', '"grab a coffee"', '"coffee chat"',
    '"would love to meet"', '"dm me"', '"ping me"', '"hit me up"', '"open to meet"',
    '"keen to meet"', '"office hours"', '"give back"', '"college talk"', 'campus',
    '"guest lecture"', 'fireside', 'meetup', '"catch up"',
]

# --- Audience / persona context ---
AUD_CORE = [
    'founders', 'founder', 'co-founder', 'cofounder', 'startup', 'startups', 'entrepreneur',
    'entrepreneurs', '"indie hacker"', 'bootstrapper', 'SaaS', 'deeptech', '"AI"',
    '"AI research"', 'ML', 'LLM', 'GenAI', 'builders', 'engineers', 'developer', 'CTO',
    'researcher', '"early stage"', '"tech community"', 'IIT', 'NIT',
]

# --- Indian Tier-2/3 cities (the geographies Shifu targets) ---
TIER2_CITIES = [
    # Andhra / Telangana (Guntur example country)
    "Guntur", "Vijayawada", "Visakhapatnam", "Warangal", "Nellore", "Tirupati", "Kakinada",
    "Rajahmundry", "Karimnagar", "Khammam", "Anantapur", "Kurnool", "Amaravati", "Eluru",
    # Tamil Nadu / Kerala
    "Coimbatore", "Madurai", "Trichy", "Salem", "Erode", "Tirunelveli", "Vellore", "Thanjavur",
    "Kochi", "Thiruvananthapuram", "Kozhikode", "Thrissur", "Kollam", "Kottayam",
    # Karnataka
    "Mysuru", "Hubli", "Mangalore", "Belgaum", "Davangere", "Gulbarga", "Shivamogga",
    # West / Central / North / East
    "Indore", "Bhopal", "Gwalior", "Jabalpur", "Ujjain", "Nagpur", "Nashik", "Aurangabad",
    "Kolhapur", "Surat", "Rajkot", "Vadodara", "Jaipur", "Jodhpur", "Udaipur", "Kota",
    "Lucknow", "Kanpur", "Varanasi", "Prayagraj", "Agra", "Meerut", "Gorakhpur", "Noida",
    "Patna", "Ranchi", "Jamshedpur", "Dhanbad", "Bhubaneswar", "Cuttack", "Raipur",
    "Dehradun", "Guwahati", "Siliguri", "Amritsar", "Jalandhar", "Ludhiana", "Bhilai",
]


def _group(items):
    return "(" + " OR ".join(items) + ")"


def _home_queries():
    meet, aud = _group(MEET_CORE[:10]), _group(AUD_CORE[:8])
    return [f"{h} {meet} {aud}" for h in HOME_TERMS]


def _occasion_queries():
    home = _group(['hometown', 'native', '"home town"', '"back home"', '"home for"', '"my ooru"', '"my gaon"'])
    aud = _group(AUD_CORE[:8])
    return [f"{o} {home} {aud}" for o in OCCASIONS]


def _intent_queries():
    """Intent-led (mentor/give-back/campus) + home/native + persona."""
    home = _group(['hometown', 'native', '"my city"', '"back home"', 'local'])
    intents = ['"mentor students"', '"give back"', '"office hours"', '"college talk"',
               '"guest lecture"', 'fireside', '"happy to mentor"', '"meet local founders"']
    aud = _group(['founders', 'startup', '"AI"', 'builders', 'students'])
    return [f"{i} {home} {aud}" for i in intents]


def city_booster_queries(cities=None):
    """City + broad travel/home vocabulary + persona/intent. India-targeted recall."""
    cities = cities or TIER2_CITIES
    travel = _group(['"my hometown"', 'native', '"home town"', '"back home"', '"heading home"',
                     'visiting', '"home for"', '"will be in"', '"landing in"', '"back in"', '"reached"'])
    aud = _group(['founder', '"AI"', 'startup', 'builder', 'meet', 'chat', 'connect', 'mentor'])
    return [f'"{c}" {travel} {aud}' for c in cities]


# Hand-crafted strong-signal queries (broad phrasings that model the example).
HANDCRAFTED = [
    '("I\'ll be in" OR "I will be in" OR "going to be in" OR "coming to" OR "landing in" OR "back in") (hometown OR native OR home OR "my ooru") (AI OR founders OR startup)',
    '("back home" OR "home for" OR "heading home" OR "going home") ("next week" OR "this week" OR "few days" OR "the holidays" OR weekend) (founders OR "AI" OR startup) (meet OR chat OR connect)',
    'visiting ("my hometown" OR "home town" OR "my native" OR "native place" OR "my city" OR "my village") (founder OR "AI research" OR startup)',
    '"native place" (visiting OR "will be in" OR "next week" OR "home for" OR reached) (meet OR chat OR connect OR guidance)',
    'anyone ("into AI" OR "in AI" OR "building AI" OR "doing ML") ("my hometown" OR "my city" OR "from here" OR "back home" OR native) (chat OR meet OR connect)',
    '("home for" OR "back for" OR "traveling for") (Diwali OR Sankranti OR Pongal OR Ugadi OR Onam OR Dussehra OR wedding) (founders OR AI OR startup OR builders)',
    '("happy to mentor" OR "give back" OR "office hours" OR "guest lecture") (hometown OR native OR "my city" OR local OR campus) (founders OR students OR builders)',
    '(coffee OR meetup OR "catch up") ("my hometown" OR "home town" OR "native place" OR "my city") (founders OR AI OR startup)',
    '"anyone on my TL" (hometown OR native OR "from" OR local) (AI OR founders OR research)',
    '("will be home" OR "going home" OR "coming home" OR "visiting home") ("next week" OR "this week" OR "few days") (founders OR AI OR startup OR builders)',
    '("in town" OR "visiting" OR "back in" OR "few days in") ("would love to" OR "happy to" OR "keen to") (meet OR chat OR connect) (founders OR AI OR startup)',
    '("dm me" OR "ping me" OR "hit me up") ("my hometown" OR "home town" OR "my city" OR "back home" OR native) (founder OR AI OR startup OR builder)',
    '("my native is" OR "my native place is" OR "hailing from" OR "i am from") (founder OR "AI" OR startup) (visiting OR "will be" OR "home" OR "next week")',
    '("working from" OR "wfh from" OR "remote from") (hometown OR native OR "my village" OR "my town") (founder OR AI OR startup OR builder)',
]


def get_queries(include_city_booster=True, include_occasion=True, include_intent=True, limit=None):
    """Default = wide + India-anchored: home + handcrafted + occasion + intent + city sweep."""
    queries = _home_queries() + HANDCRAFTED
    if include_occasion:
        queries += _occasion_queries()
    if include_intent:
        queries += _intent_queries()
    if include_city_booster:
        queries += city_booster_queries()
    seen, out = set(), []
    for q in queries:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out[:limit] if limit else out


# --- LinkedIn queries (wide, India-anchored; LinkedIn-search-bar style) ---
def get_linkedin_queries(limit=None):
    base = [
        "visiting my hometown", "back in my hometown", "coming home to my hometown",
        "my native place visiting", "home for a few days hometown founders",
        "visiting my hometown AI founders", "back home keen to meet local founders",
        "home for Diwali founders", "home for Sankranti startup", "home for Pongal founders",
        "home for the holidays founders meet", "visiting my native place meet founders",
        "back in my city happy to mentor founders", "home town trip meet local entrepreneurs",
        "in my hometown happy to connect AI", "heading home to meet local startup community",
        "family wedding hometown meet founders", "winter break hometown founders",
        "working from my hometown founder", "give back to my hometown startup community",
        "guest lecture hometown college founders", "mentoring students my hometown AI",
    ]
    key_cities = ["Guntur", "Vijayawada", "Visakhapatnam", "Warangal", "Coimbatore", "Madurai",
                  "Indore", "Nagpur", "Jaipur", "Lucknow", "Kochi", "Bhubaneswar", "Surat", "Nashik"]
    base += [f"visiting hometown {c} founders" for c in key_cities]
    return base[:limit] if limit else base


if __name__ == "__main__":
    qs = get_queries()
    print(f"X queries: {len(qs)}  (home {len(_home_queries())} + handcrafted {len(HANDCRAFTED)} "
          f"+ occasion {len(_occasion_queries())} + intent {len(_intent_queries())} + city {len(city_booster_queries())})")
    print(f"LinkedIn queries: {len(get_linkedin_queries())}")
    print(f"Tier-2/3 cities: {len(TIER2_CITIES)}")
