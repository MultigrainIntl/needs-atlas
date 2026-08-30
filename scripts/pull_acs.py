#!/usr/bin/env python3
"""
pull_acs.py — Pull ACS 5-year data at census-tract level for the Needs Atlas counties.

Uses only the Python standard library. Writes data/acs_raw.csv keyed by GEOID
(state+county+tract, 11 digits) — the join key everything downstream uses.

Run:
    python scripts/pull_acs.py                 # keyless (fine for this volume)
    CENSUS_API_KEY=xxxx python scripts/pull_acs.py   # if keyless is throttled

A free key (issued instantly) is at https://api.census.gov/data/key_signup.html
"""
import csv, json, os, sys, urllib.request, urllib.parse
from pathlib import Path

YEAR = os.environ.get("ACS_YEAR", "2023")          # ACS 5-year vintage
DATASET = "acs/acs5"
BASE = f"https://api.census.gov/data/{YEAR}/{DATASET}"
KEY = os.environ.get("CENSUS_API_KEY", "").strip()

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config" / "counties.json").read_text())
VARS = json.loads((ROOT / "config" / "acs_variables.json").read_text())
OUT = ROOT / "data" / "acs_raw.csv"

# Assemble the full list of raw variable codes we need.
codes = list(VARS["singles"].keys())
for k in ("under_200_fpl_components", "uninsured_components",
          "age_65plus_components", "lep_household_components"):
    codes += VARS[k]
codes = list(dict.fromkeys(codes))                 # de-dupe, keep order

# SNAP is pulled as its own optional request so a hiccup on it never blocks the
# core variables. Keep it out of the main code list.
SNAP_CODES = ["B22003_001E", "B22003_002E"]
codes = [c for c in codes if c not in SNAP_CODES]


def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def fetch(var_chunk, state, county):
    params = {
        "get": ",".join(var_chunk),
        "for": "tract:*",
        "in": f"state:{state} county:{county}",
    }
    if KEY:
        params["key"] = KEY
    url = f"{BASE}?{urllib.parse.urlencode(params, safe=':*')}"
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def rows_to_dicts(payload):
    header, *data = payload
    return [dict(zip(header, row)) for row in data]


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    merged = {}   # GEOID -> {var: value, ...}
    state = CFG["state_fips"]

    def absorb(payload, wanted, county):
        for d in rows_to_dicts(payload):
            geoid = d["state"] + d["county"] + d["tract"]
            rec = merged.setdefault(geoid, {"GEOID": geoid, "county_name": county["name"]})
            for c in wanted:
                rec[c] = d.get(c)

    for county in CFG["counties"]:
        cfips = county["fips"]
        # Census API allows ~50 variables/call; chunk at 45 to be safe. A failed
        # chunk is skipped with a warning rather than aborting the whole pull.
        for chunk in chunks(codes, 45):
            try:
                absorb(fetch(chunk, state, cfips), chunk, county)
            except Exception as e:
                print(f"  WARN: variable chunk failed for {county['name']}: {e}", file=sys.stderr)
        # SNAP (B22003) — optional; a failure here loses only SNAP, nothing else.
        try:
            absorb(fetch(SNAP_CODES, state, cfips), SNAP_CODES, county)
        except Exception as e:
            print(f"  WARN: SNAP (B22003) pull failed for {county['name']}: {e}", file=sys.stderr)
        print(f"  {county['name']:10s} ({cfips}) — tracts so far: "
              f"{sum(1 for g in merged if g[2:5] == cfips)}")

    if not merged:
        print("No ACS rows retrieved — leaving existing data untouched.", file=sys.stderr)
        sys.exit(1)

    fieldnames = ["GEOID", "county_name"] + codes + SNAP_CODES
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for rec in merged.values():
            w.writerow(rec)

    print(f"\nWrote {len(merged)} tract rows -> {OUT}")
    if merged:
        sample = next(iter(merged.values()))
        print("Sample row (verify codes look sane):")
        for kk in list(sample)[:8]:
            print(f"   {kk} = {sample[kk]}")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} from Census API: {e.reason}", file=sys.stderr)
        print("If 4xx, check the ACS_YEAR vintage and variable codes; if 429, "
              "set CENSUS_API_KEY.", file=sys.stderr)
        sys.exit(1)
