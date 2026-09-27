#!/usr/bin/env bash
# Regenerates every number and figure. Run from repo root. Needs ~25 GB disk, network, several hours (DEM reads dominate).
set -euo pipefail
export PYTHONPATH=src
mkdir -p data/processed figures outputs
bash src/00_download_static.sh
python3 src/00_select_study_area.py
python3 src/01_terrain.py
python3 src/02_download_fs_services.py
python3 src/02b_download_f2f.py
python3 src/03_harvest_slopes.py
python3 src/04_hazard.py
python3 src/05_water.py
python3 src/06_timber_feasibility.py
python3 src/07a_prepare_roads.py
python3 src/07b_joint_slope_road.py
cp src/08_agency_screen.py src/agency_screen.py   # figure scripts import it as a module
python3 src/08_agency_screen.py
python3 src/08a_download_dem30.py
python3 src/08b_mosaic_dem90.py
python3 src/08c_dem_resolution_check.py
for f in src/09a_fig_map.py src/09b_fig_slope.py src/09c_fig_heatmap.py src/09d_fig_hazard_water.py src/09e_fig_screen_by_forest.py; do python3 $f; done
python3 src/10_build_pdf.py
