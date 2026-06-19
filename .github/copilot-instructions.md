# Copilot instructions — Federal AI spending measurement audit

## What this project is
This repository is a **measurement audit**, not a spending tracker. It asks how
much the reported figure for U.S. federal AI spending depends on how an "AI
contract" is defined, and what the standard keyword method systematically
misses. Producing another "federal AI spend is $X and rising" number is
explicitly NOT the goal — that ground is already covered by others (e.g.
Brookings). The contribution is the transparency and reproducibility of the
method itself.

## The structure is intentional and complete — extend it, do not rebuild it
The layout below is deliberate and finished. Add to it; do not restructure,
rename, relocate, collapse, or "modernize" it. Do not introduce a web
framework, a package manager beyond pip, a build system, a database, a
notebook, or a `src/` layout. Keep dependencies to the Python standard library
plus `requests` and `pandas` (see `requirements.txt`).

- `config.py` — the single source of truth for every analytical choice: the AI
  lexicon, time window, award types, agency map, file paths. This is the
  project's "audit page" in code form.
- `classify.py` — the authoritative definition of "an AI contract": the
  tight-core lexicon applied to award descriptions with word-boundary guards.
  Contains its own precision tests.
- `fetch_usaspending.py` — a thin wrapper around the public USAspending
  award-search API. Writes `data/raw_awards.csv`.
- `analyze.py` — the audit: compares keyword-classified awards against the OMB
  2025 use-case inventory (contracted subset) and reports the divergence.
- `README.md` — states the rule and the honest limits.

## Cardinal rules (these are the ones that matter)
1. The AI definition lives ONLY in `config.py`. Never hardcode lexicon terms,
   agency names, or thresholds elsewhere. Import them from `config`.
2. `classify.py` is the authoritative rule. The API keyword filter in
   `fetch_usaspending.py` is only a volume pre-filter and is NOT the definition.
3. Preserve the word-boundary guards in `classify.py` and their tests. If you
   change the lexicon or guards, update the tests in the same change and keep
   them passing.
4. Keep outputs honest. The summary must retain its caveats: use cases are not
   dollars; DoD withholds its inventory entries; the two sources are biased in
   opposite directions. Do not delete or soften these for a cleaner headline.
5. Never invent a single "true" AI-spend number. Report ranges and the
   two-slice comparison (keyword awards vs contracted inventory).

## Tasks I want help with (all "extend," not "rebuild")
- Run and validate the live USAspending pull; confirm the API filter keys and
  field labels against current docs and fix ONLY those if they have drifted,
  without restructuring `fetch_usaspending.py`.
- Implement the broad-lexicon sensitivity band using the existing
  `LEXICON_BROAD_PHRASES` switch in `config.py`, reported alongside the tight
  headline, not replacing it.
- Add a small static results page (a single HTML file, no framework) that
  renders the files in `outputs/`.
- Expand `config.AGENCY_MATCH` coverage and the classifier's test cases.

## Constraints to respect, not refactor around
- The USAspending field labels and filter keys are the one place this can
  break. If a pull fails, adjust those values in `fetch_usaspending.py` /
  `config.py`; do not rewrite the fetch flow or add an SDK.
- This runs in plain Python from the repo root:
  `python fetch_usaspending.py` then `python analyze.py`. Keep that simplicity.

