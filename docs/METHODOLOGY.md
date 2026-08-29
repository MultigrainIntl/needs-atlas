# Methodology & sources

Everything is keyed to the **2020 census tract** (`GEOID`, 11 digits = state 34 +
county FIPS + tract). This is the universal join key across all layers and the
reason V2 patient data can drop in later without a rebuild.

## Geography
- **Counties (educated guess — confirm):** Morris (027), Sussex (037), Warren
  (041), Hunterdon (019), Somerset (035), Essex (013), Union (039).
- Replace with Zufall's official service area in `config/counties.json`.

## Sources & vintages (V1)
| Layer | Source | Endpoint | Geography | Cadence |
|---|---|---|---|---|
| Income, poverty, <200% FPL, uninsured, language, age, race | ACS 5-year | `api.census.gov/data/{year}/acs/acs5` | tract | annual |
| Chronic disease & prevention | CDC PLACES | `data.cdc.gov` (Socrata) | tract | annual |
| Composite vulnerability | CDC/ATSDR SVI | ATSDR CSV | tract | biennial |

Record the exact vintage each run (the ACS year is in the pull); cite it in grant
methodology sections.

## Indicators (ACS, from stable B/C detailed tables)
- **Poverty rate** = B17001_002E / B17001_001E
- **Under 200% FPL %** = Σ C17002_002E…007E / C17002_001E
- **Uninsured %** = Σ B27001 "no coverage" cells / B27001_001E
- **Age 65+ %** = Σ B01001 65+ cells / B01001_001E
- **Limited-English households %** = Σ C16002 LEP cells / C16002_001E
- **Race/ethnicity** = B03002 (Hispanic, and White/Black/Asian non-Hispanic)
- **Median household income** = B19013_001E

## Composite Need Score (0–100)
Five need indicators — poverty, <200% FPL, uninsured, 65+, limited-English — are
each **min-max normalized across all tracts in the 7 counties**, then averaged and
scaled to 0–100. Simple, transparent, and defensible. Swap in CDC SVI or ADI as
the backbone if a funder prefers an external index; the code is one function in
`build_need_index.py`.

## Known caveats (state these honestly in grant work)
- **Margins of error:** ACS estimates for small-population tracts have wide MOEs.
  Flag or suppress low-population tracts; never over-read a single tract.
- **Trends across 2010↔2020:** tract boundaries changed. Apply a **tract
  crosswalk** before comparing years, or the trend silently compares different
  shapes.
- **Small-cell suppression (V2):** when patient counts are added, suppress or
  mask tracts with very few patients so no one is identifiable.

## Citation format
> U.S. Census Bureau, American Community Survey 5-Year Estimates, {year},
> table {code}, census tract. Retrieved via the Census Data API.
