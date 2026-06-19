"""
fetch_usaspending.py — pull contract awards from the public USAspending API.

Run:  python fetch_usaspending.py
Output: data/raw_awards.csv

This is intentionally a thin, honest wrapper around one documented endpoint.
The server-side keyword filter only narrows the download; the real definition
is applied later by classify.py. If a field label or filter key below has
changed, check the current docs at https://api.usaspending.gov/docs/endpoints
and adjust FIELDS / the filter keys — that is the one place this can drift.
"""
import csv
import time
import sys
import requests
import config

# Fields requested from the award-search endpoint. The response keys come back
# as these exact label strings.
FIELDS = [
    "Award ID",
    "Recipient Name",
    "Awarding Agency",
    "Awarding Sub Agency",
    "Award Amount",
    "Description",
    "Contract Award Type",
    "Start Date",
    "End Date",
]


def build_payload(page: int) -> dict:
    return {
        "filters": {
            "award_type_codes": config.AWARD_TYPE_CODES,
            "time_period": config.TIME_PERIOD,
            "keywords": config.API_KEYWORD_PREFILTER,
        },
        "fields": FIELDS,
        "page": page,
        "limit": config.PAGE_SIZE,
        "sort": "Award Amount",
        "order": "desc",
    }


def fetch_all() -> list[dict]:
    url = config.API_BASE + config.AWARD_SEARCH_ENDPOINT
    rows: list[dict] = []
    for page in range(1, config.MAX_PAGES + 1):
        resp = requests.post(url, json=build_payload(page), timeout=60)
        resp.raise_for_status()
        body = resp.json()
        results = body.get("results", [])
        rows.extend(results)
        meta = body.get("page_metadata", {})
        has_next = meta.get("hasNext", meta.get("has_next_page", False))
        print(f"  page {page}: +{len(results)} rows (running total {len(rows)})")
        if not results or not has_next:
            break
        time.sleep(config.REQUEST_PAUSE_SECONDS)
    return rows


def main() -> int:
    print("Fetching contract awards from USAspending ...")
    try:
        rows = fetch_all()
    except requests.HTTPError as e:
        print(f"HTTP error from USAspending: {e}", file=sys.stderr)
        return 1
    except requests.RequestException as e:
        print(f"Network error reaching USAspending: {e}", file=sys.stderr)
        print("If you are in a restricted sandbox, allow api.usaspending.gov "
              "or run this on an unrestricted machine.", file=sys.stderr)
        return 1

    if not rows:
        print("No rows returned — check filters in config.py.", file=sys.stderr)
        return 1

    cols = FIELDS
    with open(config.RAW_AWARDS_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Wrote {len(rows)} awards -> {config.RAW_AWARDS_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
