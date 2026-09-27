# Roadless Appalachia: a reproducible technical comment

Open code and derived data behind a technical comment on USDA Forest Service docket FS-2025-0001 (proposed rescission of the 2001 Roadless Area Conservation Rule). Scope: 411 inventoried roadless area polygons (922,990 acres) in seven core Appalachian forest groupings.

The analysis covers terrain (10 m slope), the Draft EIS operability screen applied to roadless land and to Forest Service harvest units, USGS landslide susceptibility and Hurricane Helene landslide density, and drinking-water watersheds (Forests to Faucets 2.0). It does not assess carbon or biodiversity.

## Reproduce
`bash make_all.sh` downloads public inputs (see `data/SOURCES.md`) and rebuilds all tables, figures and the PDF. Save the two agency PDFs manually from Regulations.gov into `data/raw/agency/` (the site blocks scripted downloads). `data/data_manifest.csv` lists SHA-256 hashes of inputs and outputs.

## Layout
`src/` scripts run in numeric order; `data/processed/` derived tables (small CSV/JSON); `figures/` PNG and PDF; `outputs/` the comment PDF.

## Caveats
The screen bounds physical accessibility only (slope, road distance); it is not a harvest forecast. The Helene comparison is descriptive and confounded. Water populations are consumers of intakes located in a watershed, not people affected. See the comment's Section 5.

Code: MIT. Derived data: CC BY 4.0. Source datasets remain under their original public terms.
# Central-Appalachia-Roadless-Area-Analysis
