# How to add a county to Needs Atlas

The tool covers Zufall Health's 7-county service area (Essex, Hunterdon, Middlesex,
Morris, Somerset, Sussex, Warren). Adding a county is a small, well-defined job
because the whole pipeline already runs statewide — the census, CDC, County Health
Rankings and ALICE sources all cover every New Jersey county; you're just switching
one on. **No changes to the app (index.html) are needed** — the county dropdown is
built from the data, so a new county appears on its own once the data is published.

Budget: roughly 1–2 hours, most of it copying one row per source from spreadsheets
we already use.

---

## The two places that decide "which counties"

Everything keys off these two config files:

1. **`config/counties.json`** — the FIPS list. Drives the census tract pull and the
   map polygons. Add one line:

   ```json
   { "name": "Union", "fips": "039" }
   ```

2. **`config/real_counties.json`** — the county's headline figures from Census
   QuickFacts. Drives the assessment documents and the dashboard's headline numbers,
   and it's the list the assessment generator loops over. Add the county's block:
   `population, median_hh_income, poverty_pct, uninsured_under65_pct, pct_65_plus,
   pct_hispanic, pct_black`. Source: `census.gov/quickfacts/<county>countynewjersey`.

New Jersey county FIPS (the 3-digit code) for the likely candidates:

| County | FIPS | County | FIPS |
|--------|------|--------|------|
| Union    | 039 | Passaic | 031 |
| Bergen   | 003 | Hudson  | 017 |
| Ocean    | 029 | Monmouth| 025 |

(Full list: any NJ county — the state FIPS is 34, so the tract GEOID starts `34` + these 3 digits.)

---

## Add one row to each curated annual source

These are hand-maintained yearly snapshots (see `docs/` notes). For the new county,
copy its row from the same statewide source file we already pull from, keyed by the
county **name**:

- `config/food_insecurity.json` — Feeding America, Map the Meal Gap
- `config/places.json` — CDC PLACES (the county's measure→% map)
- `config/providers.json` — County Health Rankings, provider-to-population ratios
- `config/alice.json` — United For ALICE, % households below the ALICE threshold
- `config/maternal.json` — County Health Rankings, low birthweight

If a county's row is missing from one of these, the tool simply omits that metric for
that county — it never invents a number. So you can add a county with partial data and
fill the rest in later.

---

## Build and publish

Easiest path — let CI do it. Once the config files above are committed to GitHub,
open the **Actions** tab and run **"Build Atlas data"** (the "Run workflow" button).
It pulls ACS + PLACES, rebuilds `counties.json`, rebuilds the map geometry,
regenerates every county assessment, copies everything into `web/`, and commits —
which triggers the Firebase deploy. The new county is live a couple of minutes later.

Running it by hand instead (needs a free Census API key in `CENSUS_API_KEY`):

```bash
python scripts/pull_acs.py          # tract data for the new county
python scripts/pull_places.py       # (optional; committed config is used otherwise)
python scripts/build_need_index.py  # rebuilds data/counties.json + tracts_need.csv
python scripts/build_geojson.py     # map polygons (needs geopandas)
cd scripts && python generate_all_assessments.py
```

Then copy the outputs into `web/` (the CI step "Publish data to the web app" shows
exactly which files) and push.

---

## Check it landed

- The county appears in the dashboard dropdown.
- Its KPI tiles, health panel, and provider/ALICE/low-birthweight figures render.
- Its assessment opens in the in-app preview and downloads as Word.
- The tract map shows its tracts, shaded by need, with the county outline.

---

## When (not) to do this

Adding a county pays off when Zufall is considering a **site or program in that
county** — a needs assessment for it is exactly what HRSA New Access Point and
Service Area Competition applications require. Adding counties Zufall doesn't serve
adds maintenance without strengthening any grant case, so wait for a real reason.
The statewide comparison (each county's rank among all 21) is already in the tool, so
Zufall gets the statewide context without carrying extra county profiles.
