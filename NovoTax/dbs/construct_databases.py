#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import gzip
from pathlib import Path

import pandas as pd
import requests


URLS = {
    "bac120": "https://data.gtdb.aau.ecogenomic.org/releases/latest/bac120_metadata.tsv.gz",
    "ar53": "https://data.gtdb.aau.ecogenomic.org/releases/latest/ar53_metadata.tsv.gz",
}

COLUMNS_TO_KEEP = [
    'accession',
    'gtdb_representative',
    'gtdb_type_species_of_genus',
    'gtdb_taxonomy',
    'checkm2_completeness',
    'checkm2_contamination',
    'protein_count',
    'ncbi_ssu_count',
]

DOWNLOAD_DIR = Path("gtdb_downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = Path("final_reps.tsv")
COMBINED_OUTPUT_FILE = Path("gtdb_selected_metadata.tsv")


def download_file(url: str, destination: Path, chunk_size: int = 8192) -> None:
    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()

    with destination.open("wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)


def load_selected_columns_from_gzip(gz_path: Path, source_name: str) -> pd.DataFrame:
    with gzip.open(gz_path, "rt", encoding="utf-8") as f:
        df = pd.read_csv(
            f,
            sep="\t",
            usecols=COLUMNS_TO_KEEP,
            low_memory=False,
        )

    df["source"] = source_name
    return df


def safe_delete(path: Path) -> None:
    if path.exists():
        path.unlink()
        print(f"Deleted: {path}")


def add_taxonomy_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["species"] = df["gtdb_taxonomy"].str.extract(r";s__(.+)$")[0]
    df["genus"] = df["gtdb_taxonomy"].str.extract(r";g__([^;]+)")[0]
    df["family"] = df["gtdb_taxonomy"].str.extract(r";f__([^;]+)")[0]

    return df


def choose_best_fallback(family_df: pd.DataFrame) -> pd.Series | None:
    # Require SSU count to exist and not be "none" for fallback reps
    family_df = family_df[
        family_df["ncbi_ssu_count"].notna()
        & (
            family_df["ncbi_ssu_count"]
            .astype(str)
            .str.strip()
            .str.lower() != "none"
        )
    ].copy()

    if family_df.empty:
        return None

    species_reps = family_df[family_df["gtdb_representative"] == "t"].copy()
    candidate_df = species_reps if not species_reps.empty else family_df

    high_quality = candidate_df[
        (candidate_df["checkm2_completeness"] >= 95)
        & (candidate_df["checkm2_contamination"] < 1)
    ].copy()

    ranked_df = high_quality if not high_quality.empty else candidate_df

    ranked_df = ranked_df.sort_values(
        by=[
            "checkm2_contamination",
            "checkm2_completeness",
            "protein_count",
            "accession",
        ],
        ascending=[True, False, False, True],
    )

    return ranked_df.iloc[0]


def build_final_reps(df: pd.DataFrame) -> pd.DataFrame:
    # Original genus reps:
    # keep all rows where genome is both a GTDB representative
    # and the GTDB type species of its genus
    genus_reps = df[
        (df["gtdb_type_species_of_genus"] == "t")
        & (df["gtdb_representative"] == "t")
    ].copy()

    genus_reps = genus_reps.drop_duplicates(subset=["accession"])

    families_with_genus_rep = set(genus_reps["family"].dropna().unique())
    all_families = set(df["family"].dropna().unique())
    families_without_genus_rep = sorted(all_families - families_with_genus_rep)
    print(f'Number of families without representative: {len(families_without_genus_rep)}')

    fallback_rows = []
    for family in families_without_genus_rep:
        family_df = df[df["family"] == family].copy()
        if family_df.empty:
            continue
    
        chosen = choose_best_fallback(family_df)
        if chosen is not None:
            fallback_rows.append(chosen)

    if fallback_rows:
        family_fallback_reps = pd.DataFrame(fallback_rows).drop_duplicates(
            subset=["accession"]
        )
    else:
        family_fallback_reps = pd.DataFrame(columns=df.columns)

    final_reps = pd.concat(
        [genus_reps, family_fallback_reps],
        ignore_index=True,
    ).drop_duplicates(subset=["accession"])

    final_reps = final_reps.sort_values(
        by=["family", "genus", "species", "accession"]
    ).reset_index(drop=True)

    return final_reps


# def main() -> None:
all_dfs: list[pd.DataFrame] = []
downloaded_files: list[Path] = []

try:
    for source_name, url in URLS.items():
        gz_path = DOWNLOAD_DIR / f"{source_name}_metadata.tsv.gz"

        print(f"Downloading {source_name}...")
        download_file(url, gz_path)
        downloaded_files.append(gz_path)

        print(f"Loading selected columns from {source_name}...")
        df = load_selected_columns_from_gzip(gz_path, source_name)
        all_dfs.append(df)

    data = pd.concat(all_dfs, ignore_index=True)
    data = add_taxonomy_columns(data)
    
    data[COLUMNS_TO_KEEP + ["source"]].to_csv(
        COMBINED_OUTPUT_FILE,
        sep="\t",
        index=False,
    )

    print(f"Combined rows: {len(data):,}")

    # Optional diagnostic: count taxa without a GTDB representative
    tax_has_rep = (
        data.groupby("gtdb_taxonomy")["gtdb_representative"]
        .apply(lambda s: (s == "t").any())
    )
    no_rep_count = (~tax_has_rep).sum()
    print(f"Number of genus without representative: {no_rep_count:,}")

    final_reps = build_final_reps(data)

    result = final_reps[
        ["accession", "gtdb_taxonomy", "protein_count", "source"]
    ].copy()

    result = result.rename(columns={"gtdb_taxonomy": "taxonomy"})
    result.to_csv(OUTPUT_FILE, sep="\t", index=False)

    print(f"Number of final reps: {len(result):,}")
    print(f"Total protein count: {result['protein_count'].sum():,}")
    print(f"Saved: {OUTPUT_FILE}")

finally:
    print("Cleaning up downloaded files...")
    for path in downloaded_files:
        safe_delete(path)


# if __name__ == "__main__":
#     main()
