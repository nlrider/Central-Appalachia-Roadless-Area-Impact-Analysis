#!/usr/bin/env bash
# Downloads every static input used by the analysis. Idempotent: skips files that already exist.
# All sources are public U.S. government data. Retrieved 2026-09-25 for the published analysis.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/raw/{landslide,tran,agency}
fetch() { [ -s "$2" ] || { echo "downloading $2"; curl -sSL --fail -o "$2" "$1"; }; }

FS=https://data.fs.usda.gov/geodata/edw/edw_resources/shp
fetch $FS/BdyPlan_RoadlessArea_2001.zip          data/raw/BdyPlan_RoadlessArea_2001.zip          # 2001 Inventoried Roadless Areas
fetch $FS/BdyAdm_LSRS_AdministrativeForest.zip   data/raw/BdyAdm_LSRS_AdministrativeForest.zip   # administrative forest boundaries
fetch $FS/BdyOwn_LSRS_BasicOwnership.zip         data/raw/BdyOwn_LSRS_BasicOwnership.zip         # USFS-owned land parcels
fetch $FS/Trans_RoadCore_FS.zip                  data/raw/Trans_RoadCore_FS.zip                  # USFS system roads

# USGS TNM transportation (TIGER-derived), one file per state
for st in Virginia West_Virginia North_Carolina Tennessee Georgia Kentucky Pennsylvania; do
  fetch https://prd-tnm.s3.amazonaws.com/StagedProducts/Tran/Shape/TRAN_${st}_State_Shape.zip data/raw/tran/TRAN_${st}_State_Shape.zip
done

# USGS ScienceBase: landslide susceptibility (Mirus et al. 2024; item 65ccea5bd34ef4b119cb3bac) and Helene inventory (item 674634a1d34e6d1dac3abddc)
SB=https://www.sciencebase.gov/catalog/file/get
fetch "$SB/65ccea5bd34ef4b119cb3bac?name=n10_susc.zip"                 data/raw/landslide/n10_susc.zip
fetch "$SB/674634a1d34e6d1dac3abddc?name=HurricaneHelene_LS_Inventory.geojson" data/raw/landslide/helene_inventory.geojson

# unpack
for z in BdyPlan_RoadlessArea_2001 BdyAdm_LSRS_AdministrativeForest BdyOwn_LSRS_BasicOwnership; do
  [ -d data/raw/$z ] || unzip -q -o data/raw/$z.zip -d data/raw/$z
done
[ -f data/raw/landslide/n10_susc/n10_conus.tif ] || unzip -q -o data/raw/landslide/n10_susc.zip "n10_susc/n10_conus.tif" -d data/raw/landslide
for f in data/raw/tran/TRAN_*_State_Shape.zip; do
  st=$(basename "$f" _State_Shape.zip); st=${st#TRAN_}
  [ -d data/raw/tran/$st ] || { mkdir -p data/raw/tran/$st; unzip -q -o "$f" "Shape/Trans_RoadSegment*" -d data/raw/tran/$st; }
done
echo "static downloads complete"
# Agency documents (DEIS Vol. I FS-2025-0001-224064; Economic Analysis FS-2025-0001-224067) must be saved manually from Regulations.gov
# (the site blocks scripted downloads) to data/raw/agency/.
