# Needs Atlas — ArcGIS Pro heat-map recipe

A turnkey guide to turn the pipeline's tract data into a shaded need heat map in
ArcGIS Pro, publish it, and embed it in the secure site. Written to stay
**credit-conscious**: every step here is desktop analysis or feature-layer
hosting (near-zero credits) — no batch geocoding or credit-heavy tools.

**The data:** `data/tracts_need.csv` from the repo (681 census tracts across the
7 counties). The join key is **`GEOID`** — the 11-digit census-tract id
(e.g. `34027040101`; `34` = New Jersey). Everything joins on that one field.

---

## Step 1 — Start from Living Atlas tract boundaries (no download)

Don't import your own geometry — join to Esri's always-current boundaries.

1. In ArcGIS Pro, open a new Map.
2. **Add Data → Living Atlas → search "USA Census Tracts"** (the ArcGIS Living
   Atlas layer maintained by Esri). Add it.
3. Filter it to your service area so the map isn't the whole country: on that
   layer, **Definition Query** →
   `STATE_FIPS = '34' AND CNTY_FIPS IN ('013','019','023','027','035','037','041')`
   (Essex, Hunterdon, Middlesex, Morris, Somerset, Sussex, Warren). Field names
   in the Living Atlas layer vary by version — if `STATE_FIPS`/`CNTY_FIPS` aren't
   present, filter on the first 5 characters of its `GEOID` instead:
   `GEOID LIKE '34013%' OR GEOID LIKE '34019%' OR …`.

## Step 2 — Bring in the need table

1. **Add Data →** `data/tracts_need.csv`.
2. Before/at import, make sure **`GEOID` is imported as Text**, not a number
   (right-click the field in the Fields view if needed). For New Jersey the ids
   start with `34` so no leading zero is lost, but keeping it Text guarantees a
   clean string-to-string join.

## Step 3 — Join the table to the boundaries

1. Right-click the tract layer → **Joins and Relates → Add Join**.
2. **Input join field:** the layer's `GEOID`.
   **Join table:** `tracts_need.csv`. **Join field:** `GEOID`.
3. Validate the join — you should get ~681 matched tracts. (A handful of Living
   Atlas tracts with no residents may not match; that's expected.)

## Step 4 — Symbolize the need score (match the website's heat ramp)

On the joined layer: **Symbology → Graduated Colors**.

- **Field:** `need_score`
- **Method:** Manual interval, **5 classes**, with these upper breaks — they are
  the real quintiles of the data, so each color holds ~20% of tracts:

  | Class | need_score range | Color (hex) | RGB |
  |------|------------------|-------------|-----|
  | 1 — lowest need | ≤ 7.7  | `#3F8F74` | 63, 143, 116 |
  | 2 | 7.8 – 9.9  | `#8DA65E` | 141, 166, 94 |
  | 3 | 10.0 – 13.1 | `#E4B24A` | 228, 178, 74 |
  | 4 | 13.2 – 20.3 | `#DE7C3B` | 222, 124, 59 |
  | 5 — highest need | > 20.3 (to 54.6) | `#C0442E` | 192, 68, 46 |

  (Classes 2 and 4 are the midpoints of the site's teal→amber→red gradient, so
  the map and the dashboard read as the same instrument.)

- Set the outline to a thin light gray (`#D8E1DC`, ~0.3 pt) so tract shapes stay
  legible without competing with the fill.

## Step 5 — Hide the group-quarters artifacts

Seven tracts are dorms / institutional populations, not neighborhoods (they show
0% uninsured with ~100% below 200% FPL, or have almost no residents). The
website and the assessment documents both exclude them, so the map should too.

Layer **Definition Query**:

    NOT (total_pop < 1200 OR (uninsured_pct = 0 AND under_200_fpl_pct >= 90))

## Step 6 — Popups for grant screenshots

Configure the pop-up (Configure Pop-ups) to show, in order: county_name, GEOID,
need_score, uninsured_pct, under_200_fpl_pct, lep_pct, median_hh_income. That
pop-up is what you screenshot straight into an application.

---

## Making it temporal (the year slider) — do this right

A time slider needs **more than one point in time**, and there's a correct way
to build it:

- **Use non-overlapping ACS 5-year vintages:** e.g. 2010–2014, 2015–2019,
  2020–2024. The Census Bureau advises against comparing *overlapping* 5-year
  periods (2019–2023 vs 2020–2024 share four years, so "change" is mostly noise).
- **Mind the boundary change:** 2020 redistricting redrew census tracts, so
  pre-2020 vintages sit on **2010 tract boundaries** and 2020+ on **2020
  boundaries**. Keep each vintage on its own boundary layer, or crosswalk older
  data to 2020 tracts, rather than joining 2015 data to 2020 shapes.
- **The pipeline can pull these:** `scripts/pull_acs.py` already takes a year;
  extending it to loop `2014, 2019, 2024` and stamping a `year` column produces a
  stacked table. Then in ArcGIS: merge the vintages, **enable Time** on the layer
  (Layer Properties → Time → each feature has a time field = `year`), and the
  slider appears.

For now the single 2020–2024 vintage gives a complete, defensible **snapshot**
heat map — publish that, and add the time dimension when the historical vintages
are pulled. Tell me when you want the multi-year pull built.

---

## Publish and embed in the secure site

1. **Share the layer:** with the joined, symbolized layer selected, **Share As →
   Web Layer** (hosted feature layer) to your Food Aid Project ArcGIS Online org.
   Hosting a feature layer costs storage credits only (tiny for 681 polygons).
2. **Build a Web Map** in ArcGIS Online from that layer; keep the same symbology.
   (For the time slider later, use a **Web Map** with time enabled, or an
   Instant App / Dashboard with a time widget.)
3. **Embed:** copy the web map's share URL and set it in `web/index.html`:

       const ARCGIS_EMBED_URL = "https://foodaidproject.maps.arcgis.com/…";

   The site's placeholder panel is replaced by the live map automatically, then
   `firebase deploy --only hosting`.

## Credit hygiene (recap)

Desktop join + symbology = **free**. Hosting the feature layer = storage credits
only. Avoid: batch geocoding, GeoEnrichment, and credit-metered spatial-analysis
tools — none are needed here. Keep heavy analysis in ArcGIS Pro on the desktop;
publish only the finished layer.
