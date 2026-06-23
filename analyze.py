"""
analyze.py — the audit.

Two halves:
  1. Coverage divergence: keyword-classified awards vs the OMB contracted inventory.
  2. Instrumentation: annual AI awards and obligations (the adoption curve),
     defined KPIs, and a split of real growth from definitional inflation.

Run:  python analyze.py
Outputs:
  outputs/coverage_summary.txt   the divergence numbers
  outputs/annual_series.csv      year, group, awards, obligations
  outputs/agency_comparison.csv  per-agency presence in each method
  site/series-data.js            the chart data the website reads
"""
import os, re, sys, csv, json
from collections import Counter, defaultdict
import requests
import config
from classify import is_ai, matched_terms

# The original two-phrase core, kept here so we can measure how much of the
# count exists only because the lexicon was widened (definitional inflation).
CORE_PHRASES = ["artificial intelligence", "machine learning"]
_CORE_RES = [re.compile(r"\b" + re.escape(p).replace(r"\ ", r"\s+") + r"\b", re.I) for p in CORE_PHRASES]
def is_core_ai(desc): return bool(desc) and any(rx.search(desc) for rx in _CORE_RES)


# ---------- helpers ----------
def find_col(df_cols, candidates):
    for c in candidates:
        if c in df_cols: return c
    return None

def fiscal_year(date_str):
    """US federal FY starts Oct 1. Returns int FY or None."""
    m = re.match(r"\s*(\d{4})-(\d{2})", date_str or "")
    if not m: return None
    y, mo = int(m.group(1)), int(m.group(2))
    return y + 1 if mo >= 10 else y

def fy_bounds_from_time_period(periods):
    """Derive inclusive FY bounds from config.TIME_PERIOD entries."""
    if not periods:
        return None, None
    start_fys, end_fys = [], []
    for p in periods:
        start_fy = fiscal_year((p or {}).get("start_date"))
        end_fy = fiscal_year((p or {}).get("end_date"))
        if start_fy is not None:
            start_fys.append(start_fy)
        if end_fy is not None:
            end_fys.append(end_fy)
    if not start_fys or not end_fys:
        return None, None
    return min(start_fys), max(end_fys)

def to_amount(s):
    if s is None: return 0.0
    s = str(s).replace("$", "").replace(",", "").strip()
    try: return float(s)
    except ValueError: return 0.0

def is_dod(agency_name):
    return "defense" in (agency_name or "").lower()


# ---------- inventory ----------
def load_inventory_contracted():
    if not os.path.exists(config.INVENTORY_LOCAL):
        os.makedirs(os.path.dirname(config.INVENTORY_LOCAL), exist_ok=True)
        r = requests.get(config.INVENTORY_RAW_URL, timeout=120); r.raise_for_status()
        open(config.INVENTORY_LOCAL, "wb").write(r.content)
    rows = []
    with open(config.INVENTORY_LOCAL, encoding="utf-8-sig", errors="replace") as fh:
        for row in csv.DictReader(fh): rows.append(row)
    contracted = [x for x in rows
                  if (x.get("contracting_usage", "") or "").strip() in config.INVENTORY_CONTRACTED_VALUES]
    return rows, contracted


# ---------- load awards ----------
def load_awards():
    if not os.path.exists(config.RAW_AWARDS_CSV):
        print(f"Missing {config.RAW_AWARDS_CSV}. Run fetch_usaspending.py first.", file=sys.stderr)
        sys.exit(1)
    with open(config.RAW_AWARDS_CSV, encoding="utf-8", errors="replace") as fh:
        rows = list(csv.DictReader(fh))
    cols = rows[0].keys() if rows else []
    desc_c = find_col(cols, ["Description", "description", "transaction_description"])
    amt_c  = find_col(cols, ["Award Amount", "award_amount", "total_obligation"])
    ag_c   = find_col(cols, ["Awarding Agency", "awarding_agency_name"])
    date_c = find_col(cols, ["Start Date", "start_date", "Action Date", "action_date", "End Date"])
    for r in rows:
        r["_desc"] = r.get(desc_c, "") if desc_c else ""
        r["_amt"]  = to_amount(r.get(amt_c)) if amt_c else 0.0
        r["_ag"]   = r.get(ag_c, "") if ag_c else ""
        r["_fy"]   = fiscal_year(r.get(date_c)) if date_c else None
    return [r for r in rows if is_ai(r["_desc"])], (date_c is not None), (amt_c is not None)


def main():
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("site", exist_ok=True)
    awards, have_dates, have_amts = load_awards()
    fy_start, fy_end = fy_bounds_from_time_period(config.TIME_PERIOD)
    if fy_start is not None and fy_end is not None:
        awards = [a for a in awards if a["_fy"] is not None and fy_start <= a["_fy"] <= fy_end]
    all_rows, contracted = load_inventory_contracted()

    full_count = len(awards)
    core_count = sum(1 for a in awards if is_core_ai(a["_desc"]))
    defn_share = (full_count - core_count) / full_count if full_count else 0
    total_oblig = sum(a["_amt"] for a in awards)

    # ----- annual series (adoption curve) -----
    yrs = sorted({a["_fy"] for a in awards if a["_fy"]})
    series = {y: {"awards": 0, "oblig": 0.0, "dod_oblig": 0.0, "civ_oblig": 0.0,
                  "dod_awards": 0, "civ_awards": 0} for y in yrs}
    for a in awards:
        y = a["_fy"]
        if not y: continue
        s = series[y]; s["awards"] += 1; s["oblig"] += a["_amt"]
        if is_dod(a["_ag"]): s["dod_oblig"] += a["_amt"]; s["dod_awards"] += 1
        else:               s["civ_oblig"] += a["_amt"]; s["civ_awards"] += 1

    # real growth: CAGR of awards under the fixed current definition
    cagr = None
    if len(yrs) >= 2:
        first, last = series[yrs[0]]["awards"], series[yrs[-1]]["awards"]
        n = yrs[-1] - yrs[0]
        if first > 0 and n > 0: cagr = (last / first) ** (1 / n) - 1

    # ----- write annual_series.csv -----
    with open("outputs/annual_series.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["fiscal_year", "ai_awards", "ai_obligations_usd", "dod_obligations_usd", "civ_obligations_usd"])
        for y in yrs:
            s = series[y]; w.writerow([y, s["awards"], round(s["oblig"]), round(s["dod_oblig"]), round(s["civ_oblig"])])

    # ----- write site/series-data.js (the chart reads this) -----
    mm = lambda v: round(v / 1e6, 1)  # to $millions
    data = {
        "fy": yrs,
        "ai_oblig_dod": [mm(series[y]["dod_oblig"]) for y in yrs],
        "ai_oblig_civ": [mm(series[y]["civ_oblig"]) for y in yrs],
        "ai_awards":    [series[y]["awards"] for y in yrs],
        "kpi": {
            "full_count": full_count, "core_count": core_count,
            "definitional_share": round(defn_share, 3),
            "total_oblig_m": mm(total_oblig),
            "cagr_awards": round(cagr, 3) if cagr is not None else None,
        },
        "generated_from": "real pull" if have_dates and have_amts else "sample/mock",
    }
    with open("site/series-data.js", "w") as fh:
        fh.write("/* generated by analyze.py — do not edit by hand */\n")
        fh.write("window.TMG_SERIES = " + json.dumps(data, indent=2) + ";\n")

    # ----- coverage divergence (unchanged core) -----
    award_agencies = set()  # agency normalization reused from config map
    def norm(name):
        low = (name or "").lower()
        for ab, needles in config.AGENCY_MATCH.items():
            if any(n in low for n in needles): return ab
        return (name or "UNK").upper()[:24]
    for a in awards: award_agencies.add(norm(a["_ag"]))
    inv_agencies = set((x.get("agency", "") or "").strip() for x in contracted)
    overlap = award_agencies & inv_agencies
    dod_award_oblig = sum(a["_amt"] for a in awards if is_dod(a["_ag"]))
    dod_share_ct = sum(1 for a in awards if is_dod(a["_ag"])) / full_count if full_count else 0

    lines = []
    def out(s=""): lines.append(s); print(s)
    out("=" * 64); out("FEDERAL AI MEASUREMENT AUDIT"); out("=" * 64)
    out("")
    out("KPIs (defined here, computed from the pull):")
    out("  K1 AI awards            = contract awards meeting the AI rule")
    out("  K2 AI obligations       = sum of award amounts meeting the rule (obligation proxy)")
    out("  K3 DoD share            = DoD share of awards / obligations")
    out("  K4 Definitional share   = (full - core) / full, share of count owed to lexicon width")
    out("  K5 AI share of IT spend = AI obligations / IT-NAICS obligations  [needs denominator pull]")
    out("")
    out(f"Awards (9-phrase rule)            : {full_count}")
    out(f"Awards (2-phrase core, same pull) : {core_count}")
    out(f"Definitional share (K4)           : {defn_share*100:.0f}%  ({full_count-core_count} of {full_count} owe to wider lexicon)")
    out(f"Total AI obligations (K2)         : ${total_oblig/1e6:,.1f}M")
    out(f"DoD share by count (K3)           : {dod_share_ct*100:.1f}%")
    out(f"DoD share by obligations (K3)     : {dod_award_oblig/total_oblig*100:.1f}%" if total_oblig else "  n/a")
    out("")
    out("Adoption curve (K1, K2 by fiscal year):")
    out(f"  {'FY':6}{'awards':>8}{'oblig $M':>12}{'DoD $M':>10}{'civ $M':>10}")
    for y in yrs:
        s = series[y]
        out(f"  {y:<6}{s['awards']:>8}{s['oblig']/1e6:>12,.1f}{s['dod_oblig']/1e6:>10,.1f}{s['civ_oblig']/1e6:>10,.1f}")
    if cagr is not None:
        out("")
        out("Attribution — real growth vs definitional inflation:")
        out(f"  Real growth   : awards CAGR FY{yrs[0]}->FY{yrs[-1]} = {cagr*100:+.1f}% per year (fixed definition)")
        out(f"  Definitional  : {defn_share*100:.0f}% of the level is lexicon width, not growth")
    out("")
    out(f"Agencies — keyword {len(award_agencies)}, inventory {len(inv_agencies)}, overlap {len(overlap)}")
    out("")
    out("Reminder: use cases are not dollars, DoD withholds its inventory, and")
    out("Award Amount is an obligation proxy. The range and the splits are the finding.")
    open("outputs/coverage_summary.txt", "w").write("\n".join(lines) + "\n")
    print("\nWrote outputs/ and site/series-data.js")

if __name__ == "__main__":
    main()
