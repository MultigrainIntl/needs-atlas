#!/usr/bin/env python3
"""
pull_svi.py — CDC/ATSDR Social Vulnerability Index, NJ tracts, for the Atlas.

ATSDR publishes SVI as downloadable CSV per state/year. Stdlib only.
Writes data/svi_raw.csv keyed by GEOID (FIPS), keeping the four theme scores
and the overall percentile ranking.

    SVI_CSV_URL="https://svi.cdc.gov/.../NewJersey_tract.csv" python scripts/pull_svi.py

Notes:
  * ATSDR gates some downloads behind their site; the most reliable path is to
    download the "New Jersey / census tracts" CSV from
    https://www.atsdr.cdc.gov/placeandhealth/svi/data_documentation_download.html
    and pass its local path via SVI_CSV_PATH, OR host it and pass SVI_CSV_URL.
  * Column names below match recent SVI releases (RPL_THEMES = overall
    percentile). Confirm against the file header on first run.
"""
import csv, io, os, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "svi_raw.csv"

KEEP = {
    "FIPS": "GEOID",
    "RPL_THEME1": "svi_socioeconomic",
    "RPL_THEME2": "svi_household",
    "RPL_THEME3": "svi_minority_language",
    "RPL_THEME4": "svi_housing_transport",
    "RPL_THEMES": "svi_overall",
}


def load_rows():
    path = os.environ.get("SVI_CSV_PATH", "").strip()
    url = os.environ.get("SVI_CSV_URL", "").strip()
    if path:
        return list(csv.DictReader(Path(path).read_text().splitlines()))
    if url:
        with urllib.request.urlopen(url, timeout=120) as r:
            text = r.read().decode("utf-8", "replace")
        return list(csv.DictReader(io.StringIO(text)))
    raise SystemExit("Set SVI_CSV_PATH (local file) or SVI_CSV_URL to the NJ "
                     "tract SVI CSV. See header of this script for the source.")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    out = []
    for r in rows:
        rec = {}
        for src, dst in KEEP.items():
            rec[dst] = r.get(src)
        if rec.get("GEOID"):
            out.append(rec)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(KEEP.values()))
        w.writeheader()
        w.writerows(out)
    print(f"Wrote {len(out)} tract rows -> {OUT}")


if __name__ == "__main__":
    main()
