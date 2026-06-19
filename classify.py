"""
classify.py — the authoritative definition of "an AI contract."

This is deliberately small and readable. The rule is: an award counts as AI if
its description contains a tight-core AI phrase, or an isolated AI acronym.
Everything about precision (word boundaries, upper-case-only acronyms) is here
in plain sight, because the audit's whole claim is that the rule should be
visible, not hidden inside a vendor's black box or an API's opaque search.
"""
import re
import config

# Phrases: case-insensitive, whitespace-flexible, with word boundaries.
_TIGHT_PHRASE_RES = [
    re.compile(r"\b" + re.escape(p).replace(r"\ ", r"\s+") + r"\b", re.IGNORECASE)
    for p in config.LEXICON_TIGHT_PHRASES
]
_BROAD_PHRASE_RES = [
    re.compile(r"\b" + re.escape(p).replace(r"\ ", r"\s+") + r"\b", re.IGNORECASE)
    for p in config.LEXICON_BROAD_PHRASES
]

# Acronyms: matched against the ORIGINAL text, case-sensitive, isolated tokens,
# so "AI" matches "AI" but not "email", "Hawaii", or "aid".
_acronyms = list(config.LEXICON_TIGHT_ACRONYMS)
if not config.INCLUDE_BARE_AI and "AI" in _acronyms:
    _acronyms.remove("AI")
# Isolated, case-sensitive token; also reject "AI-3"-style codes (acronym + -digit)
# while still allowing "AI-enabled" / "AI-driven".
_ACRONYM_RES = [re.compile(r"(?<![A-Za-z0-9])" + re.escape(a) + r"(?![A-Za-z0-9])(?!-\d)")
                for a in _acronyms]


def matched_terms(description: str) -> list[str]:
    """Return the list of lexicon terms found in a description (may be empty)."""
    return matched_terms_with_band(description, include_broad=False)


def matched_terms_with_band(description: str, include_broad: bool = False) -> list[str]:
    """Return lexicon terms found in description; include broad phrases if enabled."""
    if not description:
        return []
    hits = []
    for rx, term in zip(_TIGHT_PHRASE_RES, config.LEXICON_TIGHT_PHRASES):
        if rx.search(description):
            hits.append(term)
    if include_broad:
        for rx, term in zip(_BROAD_PHRASE_RES, config.LEXICON_BROAD_PHRASES):
            if rx.search(description):
                hits.append(term)
    for rx, term in zip(_ACRONYM_RES, _acronyms):
        if rx.search(description):
            hits.append(term)
    return hits


def is_ai(description: str) -> bool:
    """True if the award description meets the tight-core AI rule."""
    return is_ai_with_band(description, include_broad=False)


def is_ai_with_band(description: str, include_broad: bool = False) -> bool:
    """True if the description matches the tight rule (+ optional broad phrases)."""
    return len(matched_terms_with_band(description, include_broad=include_broad)) > 0


if __name__ == "__main__":
    # Quick self-check of the precision guards.
    samples = [
        ("Machine learning platform for fraud detection", True),
        ("Repair of HVAC chiller at the Honolulu, Hawaii facility", False),
        ("Email migration and helpdesk support services", False),
        ("Computer vision pipeline for satellite imagery", True),
        ("Janitorial services, Building AI-3 loading dock", False),  # 'AI-3' not isolated
        ("Generative AI advisory services", True),
        ("Aid to families administrative support", False),
    ]
    ok = True
    for text, expected in samples:
        got = is_ai(text)
        flag = "ok" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print(f"[{flag}] is_ai={got!s:5} expected={expected!s:5} | {text}")
    print("ALL PASS" if ok else "SOME FAILED")
