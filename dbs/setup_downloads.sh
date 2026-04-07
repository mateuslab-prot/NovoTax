#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./setup_downloads.sh /path/to/output_dir
#
# What it does:
# - Creates the output directory if needed
# - Downloads files into that directory
# - Extracts .gz files in place
# - Skips downloads/extractions if files already exist

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /path/to/output_dir" >&2
  exit 1
fi

OUTDIR="$1"
mkdir -p "$OUTDIR"

download_and_extract_gz() {
  local url="$1"
  local filename="$2"

  local gz_path="$OUTDIR/$filename"
  local out_path="${gz_path%.gz}"

  if [[ -f "$gz_path" ]]; then
    echo "Already exists, skipping download: $gz_path"
  else
    echo "Downloading: $url"
    curl -L "$url" -o "$gz_path"
  fi

  if [[ -f "$out_path" ]]; then
    echo "Already extracted, skipping: $out_path"
  else
    echo "Extracting: $gz_path"
    gunzip -c "$gz_path" > "$out_path"
  fi
}

download_and_extract_gz \
  "https://data.gtdb.aau.ecogenomic.org/releases/release226/226.0/bac120_metadata_r226.tsv.gz" \
  "bac120_metadata_r226.tsv.gz"

# Placeholder examples for future downloads:
# download_and_extract_gz "https://example.org/another_file.tsv.gz" "another_file.tsv.gz"
# download_and_extract_gz "https://example.org/yet_another_file.csv.gz" "yet_another_file.csv.gz"

echo "All done."
