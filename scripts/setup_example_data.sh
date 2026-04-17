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

cat > checksums.md5 <<'EOF'
7ad67de4bd73893c9e6a9bbf5ed2509a  20181112_QX8_PhGe_SA_EasyLC12-12_B_a6_222_TP96hrs_control_rep2.mzML
9c1c6292bede0413b6fe22e3a4a1afd4  20181112_QX8_PhGe_SA_EasyLC12-14_B_a8_221_TP96hrs_control_rep1.mzML
68a1f48f17c43dc0c5071ef9c9ed7767  Biodiversity_C_Baltica_T240_R3_Inf_27Jan16_Arwen_15-07-13.mgf
0cc00aeb47a47b2a8c67dbfd3bff2285  Biodiversity_HL93_HLHfructose_aerobic_3_09Jun16_Pippin_16-03-39.mgf
b791385aa0e33e3dd28c3574a341122c  Biodiversity_P_ruminicola_MDM_anaerobic_1_09Jun16_Pippin_16-03-39.mgf
EOF

md5sum -c checksums.md5
echo "Done."
