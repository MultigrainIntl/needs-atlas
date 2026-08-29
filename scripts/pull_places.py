#!/usr/bin/env python3
"""
pull_places.py — CDC PLACES tract-level health estimates for the Atlas counties.

PLACES is published on the CDC open-data (Socrata) platform at data.cdc.gov.
Stdlib only. Writes data/places_raw.csv keyed by GEOID (LocationName = tract FIPS).

    python scripts/pull_places.py

Notes to verify on first run:
  * DATASET_ID below is the PLACES "Local Data for Better Health, Census Tract"
    release. Confirm the current id/year at data.cdc.gov (search "PLACES census
    tract"); update DATASET_ID if CDC has published a newer vintage.
  * A free Socrata app token (X-App-Token) raises rate limits but isn't required
    for this volume; set SOCRATA_APP_TOKEN to use one.
"""
import csv, json, os, urllib.request, urllib.parse
from pathlib import Path

DATASET_ID = os.environ.get("PLACES_DATASET", "cwsq-ngmh")   # PLACES tract release
BASE = f"https://data.cdc.gov/resource/{DATASET_ID}.json"
TOKEN = os.environ.get("SOCRATA_APP_TOKEN", "").strip()

# Measures to keep for V1 (PLACES short "measureid" codes).
MEASURES = ["DIABETES", "BPHIGH", "CHECKUP", "ACCESS2", "CHD", "OBESITY", "DEPRESSION"]

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config" / "counties.json").read_text())
OUT = ROOT / "data" / "places_raw.csv"

COUNTY_NAMES = [c["name"] + " County" for c in CFG["counties"]]


def query(offset, limit=5000):
    where = "stateabbr='NJ' AND measureid in ({})".format(
        ",".join(f"'{m}'" for m in MEASURES))
    params = {"$where": where, "$limit": str(limit), "$offset": str(offset)}
    url = f"{BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    if TOKEN:
        req.add_header("X-App-Token", TOKEN)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    keep_counties = set(COUNTY_NAMES)
    rows, offset = [], 0
    while True:
        batch = query(offset)
        if not batch:
            break
        for d in batch:
            if d.get("countyname") and (d["countyname"] + " County" in keep_counties
                                        or d["countyname"] in keep_counties):
                rows.append({
                    "GEOID": d.get("locationname"),      # tract FIPS
                    "county_name": d.get("countyname"),
                    "measure": d.get("measureid"),
                    "value_pct": d.get("data_value"),
                })
        offset += len(batch)
        if len(batch) < 5000:
            break

    # Pivot long -> wide: one row per GEOID, one column per measure.
    wide = {}
    for r in rows:
        w = wide.setdefault(r["GEOID"], {"GEOID": r["GEOID"],
                                         "county_name": r["county_name"]})
        w[r["measure"]] = r["value_pct"]

    fieldnames = ["GEOID", "county_name"] + MEASURES
    with OUT.open("w", newline="") as f:
        wtr = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        wtr.writeheader()
        wtr.writerows(wide.values())
    print(f"Wrote {len(wide)} tract rows -> {OUT}")


if __name__ == "__main__":
    main()
