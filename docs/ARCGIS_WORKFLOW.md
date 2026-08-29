# ArcGIS Pro workflow — the need heat map

ArcGIS Pro runs on your machine, so this is the desktop side of the build. Every
step here runs **in ArcGIS Pro (no Esri credits)**; only publishing pushes to the
ArcGIS Online org, which is credit-light.

## Prerequisites
- ArcGIS Pro, signed in as the **Named User under the Food Aid Project org**.
- The data built: run `python scripts/pull_acs.py` then
  `python scripts/build_need_index.py` → produces `data/tracts_need.csv`.

## 1 · Get 2020 census-tract boundaries for New Jersey
- Living Atlas: search **"USA Census Tract Boundaries"**, or
- TIGER/Line: Census 2020 tracts for state **34 (NJ)**.
- Filter/clip to the 7 counties (FIPS 013, 019, 027, 035, 037, 039, 041) so the
  layer matches the data.

## 2 · Join the need data to the tracts
1. **Add Data** → `data/tracts_need.csv`.
2. Confirm the join key `GEOID` is **Text** (11 characters, leading zeros intact).
   If it imported as a number, add a text field and calculate it, padding to 11.
3. Right-click the tract layer → **Joins and Relates → Add Join**:
   input field `GEOID` (tracts) = join field `GEOID` (CSV).
4. **Export Features** to a new layer to make the join permanent (cleaner for sharing).

## 3 · Symbolize the need heat map
- Symbology → **Graduated Colors** on `need_score`.
- Method: **Quantile** or **Natural Breaks**, 5 classes.
- Color scheme: a light-to-warm ramp (green → amber → red) to read as "need
  intensity." This is the static heat map.

## 4 · Make it temporal (the time slider)
The animated heat map needs multiple years stacked:
1. Re-run the pipeline for several vintages (`ACS_YEAR=2019 … 2023`), adding a
   `year` column to each `tracts_need.csv`, and append into one layer.
   *(For trends across 2010↔2020 tract lines, apply a tract crosswalk first — see
   METHODOLOGY.md.)*
2. Layer Properties → **Time** → enable, set the time field to `year`.
3. The **Time slider** appears — step/animate to watch need shift by year.

## 5 · (Optional, credit-light) travel-time access
- Add clinic locations as a point layer.
- **Network Analyst → Service Area** for 15-minute drive times (uses the local
  network dataset / ArcGIS Online routing — check credit use if using online
  routing; the desktop network dataset is free).

## 6 · Publish to the org (this is where it becomes shareable)
- **Share As → Web Layer** → *Hosted feature layer* → to the Food Aid Project org.
- Build a **Dashboard** (recommended for the embed): the need map + indicator
  charts + a county selector filter. Or a **Web Map** + Instant App.
- **Sharing: to the Organization or a Group — NOT Everyone/Public.** This keeps
  the data private and forces the login you'll wire up in the web app.

## 7 · Wire it into the website
- Copy the Dashboard / app **share URL**.
- Put it in `web/index.html` → `ARCGIS_EMBED_URL`.
- Because the layer is org-shared, viewers authenticate via ArcGIS OAuth, so the
  private data is never exposed on the open web.

## Credit discipline (recap)
- All analysis/symbology in Pro = **0 credits**.
- Hosting the tract feature layer = tiny (a few thousand small features).
- Avoid **online** spatial analysis and **batch geocoding** (that's the V2 patient
  step — geocode locally then).
