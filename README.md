# How Washington buys AI: a measurement audit

**Live site:** https://rmallorybpc.github.io/federal-ai-spend-audit/

Almost every public figure for federal AI spending is built the same way. Someone searches contract descriptions for the words artificial intelligence and adds up the dollars. This project does not try to produce a better number. It asks a different question. How much does that number depend on how you define an AI contract, and what does the standard keyword method miss?

It answers on fully open data, with the rule stated in the open in `config.py`, not buried in a vendor platform or an API keyword box.

## What it found

- The definition decides the count. On the same in-window data, 367 of 1,947 AI awards, about 19 percent, exist only because the keyword list is wider than two phrases. Move the definition and the headline moves.
- Real growth is real. AI contract obligations grew at a 25.7 percent annual rate from FY2016 to FY2025 under a fixed definition. That is adoption, not vocabulary.
- The dollars. About $2.63 billion in AI contract obligations over the window. The Defense Department is 70 percent of that by obligations and 64 percent by award count. Brookings reports about 99 percent by value; that figure is theirs, not from this pull.
- Two methods, two governments. The keyword method and the government's own use-case inventory share only 12 of the agencies each names. Eighteen civilian agencies report AI they bought by contract and never appear in the keyword results.
- The top vendor is an artifact. MathWorks, the maker of MATLAB, is the largest keyword AI vendor, very likely tool licenses caught by the words machine learning.

## The rule (stated, not hidden)

An award counts as AI if its description matches the tight core lexicon in `config.py`: artificial intelligence, machine learning, deep learning, neural network, natural language processing, computer vision, large language model, foundation model, generative AI, or an isolated acronym (AI, NLP, LLM). Word-boundary guards keep AI from matching email, Hawaii, or a building code like AI-3. The bare AI token is the noisiest term, so the pipeline reports what share of hits rely on it alone, and `INCLUDE_BARE_AI` lets you turn it off to see how much the answer moves.

This is the Tier 1, tight rule. A broader lexicon (automation, analytics, algorithm, autonomous, RPA) is configured through `LEXICON_BROAD_PHRASES` and reported as a sensitivity band alongside the tight headline, not as a replacement for it.

## The cross-check

The keyword count is compared against the OMB 2025 Federal AI Use Case Inventory, 3,611 self-reported use cases across 41 agencies, filtered to the 1,023 the government acquired by contract. The comparison surfaces what the keyword method alone cannot see: civilian agencies that report contracted AI but barely appear in keyword awards, the Defense split where DoD dominates the keyword awards but reports zero public inventory entries because it withholds them, and AI-native and hyperscaler vendors such as Microsoft, Google, and OpenAI that rarely write artificial intelligence into a contract description.

## Reproduce

```
pip install -r requirements.txt
python fetch_usaspending.py   # pulls contract awards -> data/raw_awards.csv
python analyze.py             # downloads the inventory, runs the audit
```

Outputs:

- `outputs/coverage_summary.txt`, the headline numbers, the KPIs, and the per-year curve
- `outputs/annual_series.csv`, AI awards and obligations by fiscal year
- `outputs/agency_comparison.csv`, per-agency presence in each method
- `site/series-data.js`, the chart data the live site reads

`python classify.py` runs the classifier's own precision tests.

## The site

Four pages, built on the TMG design system, deployed from `site/` by GitHub Actions:

- Overview, the adoption curve and the headline numbers
- Key findings, the four findings
- Methods, the data sources, the rule, the KPIs, and the limits
- Audit, the dated decision log and the honest limits

## Honest limits

- Use cases are not dollars. The inventory counts uses, not obligations, so the cross-check measures a gap in coverage, not a corrected total.
- Award Amount is an obligation proxy, not a final outlay.
- Both sources are biased, in opposite directions. The keyword method skews to Defense. The inventory skews civilian because Defense withholds. There is no clean ground truth, which is the point.
- The pull is filtered to the configured fiscal-year window in analysis, because USAspending returns the period-of-performance start date, which can fall outside the window. See decision D-10 on the Audit page.
- The API can drift. Field labels and filter keys for USAspending are the one place this can break. Verify against the current docs if a pull fails.

## Sources

- USAspending award search API: https://api.usaspending.gov
- OMB 2025 Federal Agency AI Use Case Inventory: https://github.com/ombegov/2025-Federal-Agency-AI-Use-Case-Inventory
