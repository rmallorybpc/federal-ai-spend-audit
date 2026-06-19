"""
analyze.py — the audit. Compares two ways of counting federal AI:

  (1) keyword-classified contract awards (USAspending, via fetch + classify)
  (2) AI use cases the government acquired by contract (OMB 2025 inventory)

and reports how far apart they are: agency overlap, the DoD inversion, vendor
divergence, and how much the award count leans on the noisy bare-"AI" token.

Run:  python analyze.py
Outputs: outputs/agency_comparison.csv, outputs/coverage_summary.txt
"""
import os
import sys
import csv
from collections import Counter

import requests
import pandas as pd

import config
from classify import is_ai, matched_terms


# --- load the OMB inventory (download once if absent) ------------------------
def load_inventory() -> pd.DataFrame:
    if not os.path.exists(config.INVENTORY_LOCAL):
        os.makedirs(os.path.dirname(config.INVENTORY_LOCAL), exist_ok=True)
        print("Downloading OMB 2025 inventory ...")
        r = requests.get(config.INVENTORY_RAW_URL, timeout=120)
        r.raise_for_status()
        with open(config.INVENTORY_LOCAL, "wb") as fh:
            fh.write(r.content)
    df = pd.read_csv(config.INVENTORY_LOCAL, encoding="utf-8-sig", dtype=str).fillna("")
    return df


def normalize_agency(name: str) -> str:
    """Map a USAspending agency name to an inventory-style abbreviation."""
    low = (name or "").lower()
    for abbrev, needles in config.AGENCY_MATCH.items():
        if any(n in low for n in needles):
            return abbrev
    return (name or "UNKNOWN").upper()[:24]


def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


# --- classify the awards side ------------------------------------------------
def load_classified_awards() -> pd.DataFrame:
    if not os.path.exists(config.RAW_AWARDS_CSV):
        print(f"Missing {config.RAW_AWARDS_CSV}. Run fetch_usaspending.py first.",
              file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(config.RAW_AWARDS_CSV, dtype=str).fillna("")
    desc = find_col(df, ["Description", "description", "transaction_description"])
    if desc is None:
        print("No description column found in awards file.", file=sys.stderr)
        sys.exit(1)
    df["_terms"] = df[desc].apply(matched_terms)
    df["_is_ai"] = df["_terms"].apply(lambda t: len(t) > 0)
    # flag awards whose ONLY reason for inclusion is the bare "AI" token
    df["_ai_only"] = df["_terms"].apply(lambda t: t == ["AI"])
    return df[df["_is_ai"]].copy()


# --- the comparison ----------------------------------------------------------
def main() -> int:
    inv = load_inventory()
    inv_contracted = inv[inv["contracting_usage"].isin(config.INVENTORY_CONTRACTED_VALUES)]

    awards = load_classified_awards()
    a_agency_col = find_col(awards, ["Awarding Agency", "awarding_agency_name"])
    a_recip_col = find_col(awards, ["Recipient Name", "recipient_name"])
    awards["_abbrev"] = awards[a_agency_col].apply(normalize_agency)

    award_agencies = set(awards["_abbrev"])
    inv_agencies = set(inv_contracted["agency"])

    overlap = award_agencies & inv_agencies
    only_inv = inv_agencies - award_agencies
    only_awd = award_agencies - inv_agencies

    n_awards = len(awards)
    n_ai_only = int(awards["_ai_only"].sum())
    dod_awards = int((awards["_abbrev"] == "DOD").sum())
    dod_inv = int((inv_contracted["agency"] == "DOD").sum())

    # vendor / recipient divergence
    top_recipients = Counter(awards[a_recip_col]).most_common(10)
    top_vendors = Counter(
        v for v in inv_contracted["vendor_name"]
        if v and v.lower() not in ("n/a", "na", "none", "none of the above", "not applicable")
    ).most_common(10)

    # write agency comparison table
    with open(config.OUT_AGENCY_COMPARISON, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["agency", "in_keyword_awards", "in_contracted_inventory"])
        for ag in sorted(award_agencies | inv_agencies):
            w.writerow([ag, ag in award_agencies, ag in inv_agencies])

    # write summary
    lines = []
    def out(s=""):
        lines.append(s)
        print(s)

    out("=" * 64)
    out("FEDERAL AI MEASUREMENT AUDIT — coverage divergence")
    out("=" * 64)
    out(f"Keyword-classified contract awards (tight rule): {n_awards}")
    out(f"  of which matched on bare 'AI' only: {n_ai_only} "
        f"({100*n_ai_only/n_awards:.0f}% precision risk)" if n_awards else "  (no awards)")
    out(f"Contracted AI use cases in OMB inventory: {len(inv_contracted)}")
    out("")
    out(f"Agencies in keyword awards: {len(award_agencies)}")
    out(f"Agencies in contracted inventory: {len(inv_agencies)}")
    out(f"  overlap: {len(overlap)}  |  inventory-only: {len(only_inv)}  "
        f"|  awards-only: {len(only_awd)}")
    out(f"  inventory-only agencies (AI use the keyword method may miss): "
        f"{', '.join(sorted(only_inv)) or '(none)'}")
    out("")
    out("The DoD inversion:")
    out(f"  DoD share of keyword awards: {100*dod_awards/n_awards:.1f}%" if n_awards else "  n/a")
    out(f"  DoD share of contracted inventory: {100*dod_inv/len(inv_contracted):.1f}%"
        if len(inv_contracted) else "  n/a")
    out("")
    out("Top recipients (keyword awards):")
    for name, c in top_recipients:
        out(f"  {c:4d}  {name[:50]}")
    out("Top vendors (contracted inventory):")
    for name, c in top_vendors:
        out(f"  {c:4d}  {name[:50]}")
    out("")
    out("Reminder: use cases are not dollars, and DoD withholds its inventory")
    out("entries — so the two sources are biased in opposite directions. The")
    out("gap between them is the finding, not a corrected 'true' number.")

    with open(config.OUT_SUMMARY, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nWrote {config.OUT_AGENCY_COMPARISON} and {config.OUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
