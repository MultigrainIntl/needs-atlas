#!/usr/bin/env python3
"""
build_need_index.py — Turn data/acs_raw.csv into data/tracts_need.csv:
derived rates plus a 0–100 composite Need Score, keyed by GEOID for ArcGIS.

Stdlib only. Run after pull_acs.py:
    python scripts/build_need_index.py
"""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARS = json.loads((ROOT / "config" / "acs_variables.json").read_text())
RAW = ROOT / "data" / "acs_raw.csv"
OUT = ROOT / "data" / "tracts_need.csv"

# The indicators that make up the composite tract Need Score (higher = more need).
# All are census-tract ACS rates, min-max-normalized then averaged.
NEED_INDICATORS = ["under_200_fpl_pct", "uninsured_pct",
                   "pov_rate", "pct_65_plus", "lep_pct", "snap_pct"]


def num(v):
    try:
        f = float(v)
        return f if f > -600000000 else None    # Census null sentinels are large negatives
    except (TypeError, ValueError):
        return None


def sum_codes(row, codes):
    total = 0.0
    for c in codes:
        v = num(row.get(c))
        if v is None:
            return None
        total += v
    return total


def pct(numer, denom):
    if numer is None or denom in (None, 0):
        return None
    return round(100.0 * numer / denom, 2)


def derive(row):
    pop = num(row.get("B01003_001E"))
    out = {
        "GEOID": row["GEOID"],
        "county_name": row.get("county_name", ""),
        "total_pop": int(pop) if pop is not None else None,
        "median_hh_income": num(row.get("B19013_001E")),
        "pov_rate": pct(num(row.get("B17001_002E")), num(row.get("B17001_001E"))),
        "under_200_fpl_pct": pct(sum_codes(row, VARS["under_200_fpl_components"]),
                                 num(row.get("C17002_001E"))),
        "uninsured_pct": pct(sum_codes(row, VARS["uninsured_components"]),
                             num(row.get("B27001_001E"))),
        "pct_65_plus": pct(sum_codes(row, VARS["age_65plus_components"]),
                           num(row.get("B01001_001E"))),
        "lep_pct": pct(sum_codes(row, VARS["lep_household_components"]),
                       num(row.get("C16002_001E"))),
        "snap_pct": pct(num(row.get("B22003_002E")), num(row.get("B22003_001E"))),
        "pct_hispanic": pct(num(row.get("B03002_012E")), num(row.get("B03002_001E"))),
        "pct_black_nh": pct(num(row.get("B03002_004E")), num(row.get("B03002_001E"))),
        "pct_white_nh": pct(num(row.get("B03002_003E")), num(row.get("B03002_001E"))),
        "pct_asian_nh": pct(num(row.get("B03002_006E")), num(row.get("B03002_001E"))),
    }
    return out


def minmax_normalize(rows, field):
    vals = [r[field] for r in rows if r.get(field) is not None]
    if not vals:
        return {r["GEOID"]: None for r in rows}
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    return {r["GEOID"]: (None if r.get(field) is None else (r[field] - lo) / span)
            for r in rows}


def main():
    if not RAW.exists():
        raise SystemExit("data/acs_raw.csv not found — run pull_acs.py first.")

    with RAW.open() as f:
        rows = [derive(r) for r in csv.DictReader(f)]

    # Composite Need Score = mean of min-max-normalized need indicators, x100.
    norms = {ind: minmax_normalize(rows, ind) for ind in NEED_INDICATORS}
    for r in rows:
        parts = [norms[ind][r["GEOID"]] for ind in NEED_INDICATORS]
        parts = [p for p in parts if p is not None]
        r["need_score"] = round(100 * sum(parts) / len(parts), 1) if parts else None

    fieldnames = list(rows[0].keys())
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    # ---- County rollup (unified source for dashboard + assessment) ----
    import json as _json
    from collections import defaultdict
    by_c = defaultdict(list)
    for r in rows:
        by_c[r["county_name"]].append(r)

    def wmean(rs, field):
        num = den = 0.0
        for r in rs:
            v, p = r.get(field), r.get("total_pop")
            if v is not None and p:
                num += v * p; den += p
        return round(num / den, 1) if den else None

    counties = []
    for name, rs in sorted(by_c.items()):
        pop = sum((r["total_pop"] or 0) for r in rs)
        counties.append({
            "county": name, "population": pop, "tracts": len(rs),
            "median_hh_income": int(wmean(rs, "median_hh_income") or 0),
            "poverty_pct": wmean(rs, "pov_rate"),
            "under_200_fpl_pct": wmean(rs, "under_200_fpl_pct"),
            "uninsured_pct": wmean(rs, "uninsured_pct"),
            "lep_pct": wmean(rs, "lep_pct"),
            "snap_pct": wmean(rs, "snap_pct"),
            "pct_65_plus": wmean(rs, "pct_65_plus"),
            "pct_hispanic": wmean(rs, "pct_hispanic"),
            "pct_black": wmean(rs, "pct_black_nh"),
        })

    # Overlay authoritative county headline figures from Census QuickFacts
    # (config/real_counties.json) — the same published county values the assessment
    # documents cite, so the dashboard and the docs never disagree. This also avoids
    # aggregating tract medians (e.g. median income), which is statistically invalid.
    # Tract-only figures (200% FPL, SNAP, LEP) and the map keep the live tract pipeline.
    RC = ROOT / "config" / "real_counties.json"
    if RC.exists():
        rc = {c["county"]: c for c in _json.loads(RC.read_text()).get("counties", [])}
        _map = {"population": "population", "median_hh_income": "median_hh_income",
                "poverty_pct": "poverty_pct", "uninsured_pct": "uninsured_under65_pct",
                "pct_65_plus": "pct_65_plus", "pct_hispanic": "pct_hispanic",
                "pct_black": "pct_black"}
        for c in counties:
            q = rc.get(c["county"], {})
            for dst, src in _map.items():
                if q.get(src) is not None:
                    c[dst] = q[src]

    # Attach county food-insecurity estimates (Feeding America — Map the Meal Gap).
    # County-level only (no tract breakdown), so it joins the county rollup here.
    fi_meta = None
    FI = ROOT / "config" / "food_insecurity.json"
    if FI.exists():
        fj = _json.loads(FI.read_text())
        fi_meta = {"source": fj.get("source"), "source_url": fj.get("source_url"),
                   "data_year": fj.get("data_year")}
        fic = fj.get("counties", {})
        for c in counties:
            d = fic.get(c["county"], {})
            c["food_insecurity_pct"] = d.get("food_insecurity_pct")
            c["child_food_insecurity_pct"] = d.get("child_food_insecurity_pct")
            c["food_insecure_people"] = d.get("food_insecure_people")

    # County Need Index: min-max of poverty + uninsured + food insecurity across the
    # seven counties, averaged x100 (relative ranking; 100 = highest, 0 = lowest).
    index_keys = ("poverty_pct", "uninsured_pct", "food_insecurity_pct")
    for key in index_keys:
        vals = [c[key] for c in counties if c.get(key) is not None]
        lo, hi = (min(vals), max(vals)) if vals else (0, 1); span = (hi - lo) or 1.0
        for c in counties:
            c.setdefault("_n", []).append(((c[key] - lo) / span) if c.get(key) is not None else 0)
    for c in counties:
        n = c.pop("_n"); c["need_index"] = round(100 * sum(n) / len(n), 1)
    (OUT.parent / "counties.json").write_text(_json.dumps(
        {"generated": __import__("datetime").date.today().isoformat(),
         "source": "ACS 5-year via Needs Atlas pipeline",
         "food_insecurity_source": fi_meta, "counties": counties}, indent=2))
    print(f"Wrote county rollup ({len(counties)} counties) -> data/counties.json")

    scored = [r["need_score"] for r in rows if r["need_score"] is not None]
    print(f"Wrote {len(rows)} tracts -> {OUT}")
    if scored:
        top = sorted((r for r in rows if r["need_score"] is not None),
                     key=lambda r: r["need_score"], reverse=True)[:5]
        print(f"Need Score range: {min(scored)}–{max(scored)}")
        print("Highest-need tracts:")
        for r in top:
            print(f"   {r['GEOID']} {r['county_name']:9s} "
                  f"score {r['need_score']}  uninsured {r['uninsured_pct']}%  "
                  f"<200%FPL {r['under_200_fpl_pct']}%")


if __name__ == "__main__":
    main()
