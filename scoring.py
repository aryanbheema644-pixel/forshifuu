"""Deterministic scoring on top of the LLM's semantic judgment.

intent_score (0-3): requires a hometown visit; strength set by openness.
persona_value (1-3) + tier label: founder/senior_tech = high, big_lab = medium, else low.
final_score = intent_score * persona_value  (0-9), used to rank leads.
"""

_OPENNESS_TO_INTENT = {"explicit": 3, "soft": 2, "none": 1}
_PERSONA = {
    "founder": (3, "high"),
    "senior_tech": (3, "high"),
    "big_lab": (2, "medium"),
    "other": (1, "low"),
}


def intent_score(judgment: dict) -> int:
    if not judgment.get("hometown_visit"):
        return 0  # not a hometown visitor => not a HomeTownTalks lead
    return _OPENNESS_TO_INTENT.get(judgment.get("openness", "none"), 1)


def persona_value_and_tier(judgment: dict):
    return _PERSONA.get(judgment.get("persona", "other"), (1, "low"))


def score(judgment: dict) -> dict:
    isc = intent_score(judgment)
    pval, tier = persona_value_and_tier(judgment)
    return {
        "intent_score": isc,
        "persona_tier": tier,
        "persona_value": pval,
        "final_score": isc * pval,
    }
