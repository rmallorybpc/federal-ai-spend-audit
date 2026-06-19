# How Washington Buys AI — a measurement audit

Almost every public figure for U.S. federal AI spending is built the same way:
search contract descriptions for the words "artificial intelligence," count the
dollars. This project does not try to produce a better number. It asks a
different question:

> **How much does the headline depend on how you define an "AI contract,"
> and what does the standard keyword method systematically miss?**

It answers that on fully open data, with the definition stated in the open
(`config.py`) rather than buried in a vendor platform or an API's keyword box.

## The rule (stated, not hidden)

An award counts as AI if its description matches the **tight core** lexicon in
`config.py` — `artificial intelligence`, `machine learning`, `deep learning`,
`neural network`, `natural language processing`, `computer vision`,
`large language model`, `foundation model`, `generative AI` — or an isolated
acronym (`AI`, `NLP`, `LLM`). Word-boundary guards keep `AI` from matching
`email`, `Hawaii`, or building codes like `AI-3`. The bare `AI` token is the
noisiest term, so the pipeline reports what share of hits rely on it alone, and
`INCLUDE_BARE_AI` lets you turn it off to see how much the answer moves.

This is the Tier 1 ("tight") rule. A broader lexicon (automation, analytics,
algorithm, autonomous, RPA) is configured through
`LEXICON_BROAD_PHRASES` and reported as a sensitivity band alongside the tight
headline, not as a replacement for it.

## The cross-check

The keyword count is compared against the **OMB 2025 Federal AI Use Case
Inventory** — 3,611 self-reported use cases across 41 agencies — filtered to the
1,023 the government acquired by contract. The comparison surfaces three things
the keyword method alone cannot see: agencies that report contracted AI use but
barely appear in keyword awards, the Defense Department inversion (≈99% of
keyword AI dollars vs 0% of the public inventory, which DoD withholds), and
AI-native / hyperscaler vendors (Microsoft, Google, OpenAI, AWS) that rarely
say "artificial intelligence" in a contract description.

## Reproduce

```bash
pip install -r requirements.txt
python fetch_usaspending.py   # pulls contract awards -> data/raw_awards.csv
python analyze.py             # downloads the inventory, runs the audit
```

Outputs land in `outputs/`:
- `coverage_summary.txt` — the headline divergence numbers
- `agency_comparison.csv` — per-agency presence in each method

`python classify.py` runs the classifier's own precision tests.

## Honest limits

- **Use cases are not dollars.** The inventory counts uses, not obligations, so
  this measures a gap in *breadth and civilian coverage*, not a corrected total.
- **Both sources are biased, in opposite directions.** Keyword-on-contracts
  skews to DoD; the inventory skews civilian because DoD withholds. There is no
  clean ground truth — which is the point.
- **The API can drift.** Field labels and filter keys for USAspending are the
  one place this can break; verify against the current docs if a pull fails.

## Sources
- USAspending award search API — https://api.usaspending.gov
- OMB 2025 Federal Agency AI Use Case Inventory —
  https://github.com/ombegov/2025-Federal-Agency-AI-Use-Case-Inventory
