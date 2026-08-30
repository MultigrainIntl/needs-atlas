#!/usr/bin/env python3
"""
build_geojson.py — Build web/tracts.geojson: census-tract polygons for the 7
service-area counties, joined to the need score, simplified for the web map.

Runs in CI (GitHub Actions), where www2.census.gov is reachable — the Cowork
container is walled off from Census servers. Needs geopandas (installed in the
workflow step). Safe to skip if the download fails: the site map degrades to the
tract heat-grid.
"""
import csv, json, urllib.request
from pathlib import Path
import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config" / "counties.json").read_text())
STATE = CFG["state_fips"]                       # "34"
CFIPS = {c["fips"] for c in CFG["counties"]}     # {'013','019',...}
TRACTS_CSV = ROOT / "data" / "tracts_need.csv"
OUT = ROOT / "web" / "tracts.geojson"
URL = f"https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_{STATE}_tract_500k.zip"


def main():
    # 1. Download the generalized tract boundaries for NJ.
    zf = ROOT / "data" / "_nj_tracts.zip"
    print(f"Downloading {URL} ...")
    zf.write_bytes(urllib.request.urlopen(URL, timeout=180).read())

    # 2. Read, filter to the 7 counties, reproject to WGS84, simplify for the web.
    gdf = gpd.read_file(f"zip://{zf}")
    gdf = gdf[gdf["COUNTYFP"].isin(CFIPS)][["GEOID", "geometry"]].copy()
    gdf = gdf.to_crs(4326)
    gdf["geometry"] = gdf.geometry.simplify(0.0004, preserve_topology=True)

    # 3. Join the need data.
    cols = ["GEOID", "county_name", "need_score", "uninsured_pct",
            "under_200_fpl_pct", "total_pop"]
    if TRACTS_CSV.exists():
        df = pd.read_csv(TRACTS_CSV, dtype={"GEOID": str})[cols]
        gdf = gdf.merge(df, on="GEOID", how="left")

    # 4. Write GeoJSON (trimmed coordinate precision keeps the file small).
    OUT.parent.mkdir(exist_ok=True)
    gdf.to_file(OUT, driver="GeoJSON", coordinate_precision=5)
    kb = OUT.stat().st_size / 1024
    print(f"Wrote {len(gdf)} tracts -> {OUT} ({kb:.0f} KB)")


if __name__ == "__main__":
    main()
