#!/usr/bin/env bash
set -euo pipefail

RECORD_ID="19495971"
OUTDIR="${1:-data}"
BASE_URL="https://zenodo.org/records/${RECORD_ID}/files"

mkdir -p "$OUTDIR"
cd "$OUTDIR"

download() {
  local file="$1"
  if [ -f "$file" ]; then
    echo "Already exists: $file"
  else
    echo "Downloading $file"
    curl -L --fail --retry 3 --retry-delay 5 \
      -o "$file" \
      "${BASE_URL}/${file}?download=1"
  fi
}

download "20181112_QX8_PhGe_SA_EasyLC12-12_B_a6_222_TP96hrs_control_rep2.mzML"
download "20181112_QX8_PhGe_SA_EasyLC12-14_B_a8_221_TP96hrs_control_rep1.mzML"
download "Biodiversity_C_Baltica_T240_R3_Inf_27Jan16_Arwen_15-07-13.mgf"
download "Biodiversity_HL93_HLHfructose_aerobic_3_09Jun16_Pippin_16-03-39.mgf"
download "Biodiversity_P_ruminicola_MDM_anaerobic_1_09Jun16_Pippin_16-03-39.mgf"

echo "Done."
