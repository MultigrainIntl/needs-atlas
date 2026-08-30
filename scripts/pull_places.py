#!/usr/bin/env python3
"""
pull_places.py — Refresh config/places.json from CDC PLACES (county data).

PLACES publishes model-based small-area estimates of chronic disease, health
status, prevention, and social conditions, built from BRFSS. We pull the crude
prevalence for a curated, grant-relevant set of measures for the seven Needs
Atlas counties, plus a population-weighted New Jersey comparison computed across
all 21 NJ counties.

Stdlib only. Runs on CI (GitHub Actions can reach data.cdc.gov). If the pull
fails, the committed config/places.json is left untouched so the build still has
data — same resilience principle as the rest of the pipeline.

    python scripts/pull_places.py
"""
import json, sys, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "config" / "places.json"

# Current PLACES county dataset (long format). Update the id when a newer
# release supersedes it (discover via the Socrata catalog on data.cdc.gov).
DATASET = "swc5-untb"          # PLACES: Local Data for Better Health, County Data
RELEASE = "2025"
BASE = f"https://data.cdc.gov/resource/{DATASET}.json"

OUR = ["Essex", "Hunterdon", "Middlesex", "Morris", "Somerset", "Sussex", "Warren"]

# Curated measures — all oriented so a HIGHER value means MORE need.
LABELS = {
    "DIABETES": "Diabetes", "OBESITY": "Obesity", "BPHIGH": "High blood pressure",
    "HIGHCHOL": "High cholesterol", "CHD": "Coronary heart disease", "STROKE": "Stroke",
    "CASTHMA": "Current asthma", "COPD": "COPD", "CANCER": "Cancer (non-skin)",
    "ARTHRITIS": "Arthritis", "DEPRESSION": "Depression", "GHLTH": "Fair or poor health",
    "MHLTH": "Frequent mental distress", "ACCESS2": "No health insurance (18–64)",
    "LACKTRPT": "Lack of transportation", "FOODINSECU": "Food insecurity (self-reported)",
    "HOUSINSECU": "Housing insecurity",
}
ORDER = list(LABELS.keys())


def fetch_nj_crude():
    params = {
        "stateabbr": "NJ",
        "datavaluetypeid": "CrdPrv",
        "$limit": "5000",
        "$select": "locationname,measureid,data_value,totalpopulation",
    }
    url = f"{BASE}?{urllib.parse.urlencode(params, safe='$:,')}"
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.load(r)


def main():
    rows = fetch_nj_crude()
    by, pop = {}, {}
    for d in rows:
        c = d.get("locationname"); m = d.get("measureid")
        v = d.get("data_value")
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        by.setdefault(c, {})[m] = v
        try:
            pop[c] = float(d.get("totalpopulation") or 0)
        except (TypeError, ValueError):
            pop[c] = pop.get(c, 0)

    if not by:
        print("No PLACES rows returned — leaving config/places.json untouched.", file=sys.stderr)
        sys.exit(1)

    # NJ population-weighted average across all counties returned.
    nj = {}
    for m in ORDER:
        num = den = 0.0
        for c, mv in by.items():
            v = mv.get(m); p = pop.get(c, 0)
            if v is not None and p:
                num += v * p; den += p
        nj[m] = round(num / den, 1) if den else None

    counties = {}
    for c in OUR:
        mv = by.get(c, {})
        counties[c] = {m: (round(mv[m], 1) if m in mv else None) for m in ORDER}

    out = {
        "source": f"CDC PLACES, {RELEASE} release (model-based small-area estimates from BRFSS)",
        "source_url": "https://www.cdc.gov/places/",
        "dataset": f"data.cdc.gov/resource/{DATASET} (County Data)",
        "release": RELEASE,
        "data_value_type": "Crude prevalence (% of adults)",
        "comparison": "NJ = population-weighted average across all 21 NJ counties",
        "measure_order": ORDER,
        "measures": LABELS,
        "nj": nj,
        "counties": counties,
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT} — {len(ORDER)} measures x {len(OUR)} counties (release {RELEASE}).")
    print(f"  Essex diabetes {counties['Essex'].get('DIABETES')} vs NJ {nj.get('DIABETES')}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"PLACES pull failed ({e}); keeping existing config/places.json.", file=sys.stderr)
        sys.exit(1)
