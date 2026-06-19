"""
config.py — every choice this study makes, in one place.

The whole point of this project is that "federal AI spending" is not a number
you read off a database; it is a number you CONSTRUCT by choosing a definition.
So the definition lives here, in the open, instead of being buried in code.
Change a value here and re-run; the outputs change with it. That is the audit.
"""

# --- USAspending pull ---------------------------------------------------------
API_BASE = "https://api.usaspending.gov"
AWARD_SEARCH_ENDPOINT = "/api/v2/search/spending_by_award/"

# Window agreed for the study. USAspending uses fiscal-year action dates.
TIME_PERIOD = [{"start_date": "2015-10-01", "end_date": "2025-09-30"}]

# Contract award types only (definitive contracts, purchase orders, delivery
# orders, BPA calls). Grants/loans are a separate question; excluded here.
AWARD_TYPE_CODES = ["A", "B", "C", "D"]

# Server-side keyword pre-filter, used ONLY to keep the download small.
# It is NOT the definition. The authoritative rule is the explicit, word-boundary
# classifier in classify.py, applied to each award description after download.
API_KEYWORD_PREFILTER = ["artificial intelligence", "machine learning"]

# How many pages of 100 to pull before stopping (raise for a full run).
MAX_PAGES = 50
PAGE_SIZE = 100
REQUEST_PAUSE_SECONDS = 0.5  # be polite to a public API

# --- The definition rule (Tier 1, "tight core") ------------------------------
# Multi-word phrases are matched case-insensitively.
LEXICON_TIGHT_PHRASES = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural network",
    "natural language processing",
    "computer vision",
    "large language model",
    "foundation model",
    "generative ai",
    "generative artificial intelligence",
]
# Bare acronyms are matched ONLY as isolated, upper-case tokens, to avoid
# catching substrings (e.g. "AI" inside "chair", "email", "Hawaii").
# NOTE: bare "AI" still carries precision risk; toggle below to study its effect.
LEXICON_TIGHT_ACRONYMS = ["AI", "NLP", "LLM"]
INCLUDE_BARE_AI = True  # flip to False to see how much the headline depends on it

# Placeholder for the sensitivity band. Left empty on purpose: the "broad"
# lexicon (automation, analytics, algorithm, autonomous, RPA, ...) is a future
# switch, not the headline. Keeping it visible documents the choice not made.
LEXICON_BROAD_PHRASES: list[str] = []

# --- OMB 2025 AI Use Case Inventory (the cross-check) ------------------------
INVENTORY_RAW_URL = (
    "https://raw.githubusercontent.com/ombegov/"
    "2025-Federal-Agency-AI-Use-Case-Inventory/main/"
    "Data/2025_individually_reported_AI_use_cases.csv"
)
INVENTORY_LOCAL = "data/2025_individually_reported_AI_use_cases.csv"
# Use cases the government acquired by contract — the subset comparable to
# contract spend. (In-house builds are excluded from the contract comparison.)
INVENTORY_CONTRACTED_VALUES = ["Vendor Purchased", "Contracting and In House"]

# --- Files -------------------------------------------------------------------
RAW_AWARDS_CSV = "data/raw_awards.csv"
OUT_AGENCY_COMPARISON = "outputs/agency_comparison.csv"
OUT_SUMMARY = "outputs/coverage_summary.txt"

# --- Agency normalization ----------------------------------------------------
# USAspending reports full agency names; the inventory uses abbreviations.
# This is a partial, easily extended map: abbrev -> substrings to look for in a
# USAspending "Awarding Agency" name (lower-cased, first match wins).
AGENCY_MATCH = {
    "DOD":   ["defense"],
    "HHS":   ["health and human services"],
    "NASA":  ["aeronautics and space", "nasa"],
    "VA":    ["veterans affairs"],
    "DOE":   ["department of energy"],
    "DOJ":   ["justice"],
    "DOI":   ["interior"],
    "DHS":   ["homeland security"],
    "DOC":   ["commerce"],
    "USDA":  ["agriculture"],
    "TREAS": ["treasury"],
    "DOT":   ["transportation"],
    "SEC":   ["securities and exchange"],
    "STATE": ["department of state"],
    "ED":    ["education"],
    "SBA":   ["small business"],
    "SSA":   ["social security"],
    "FTC":   ["federal trade"],
    "FDIC":  ["federal deposit"],
    "TVA":   ["tennessee valley"],
}
