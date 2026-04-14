#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import gzip
import os
from pathlib import Path

import pandas as pd
import requests

from NovoTax.dbs.create_db import build_mmseqs_db, process_fasta_folder_to_single
from NovoTax.dbs.ncbi import NCBIProteomeDownloader


URLS = {
    "bac120": "https://data.gtdb.aau.ecogenomic.org/releases/latest/bac120_metadata.tsv.gz",
    "ar53": "https://data.gtdb.aau.ecogenomic.org/releases/latest/ar53_metadata.tsv.gz",
}

COLUMNS_TO_KEEP = [
    "accession",
    "gtdb_representative",
    "gtdb_type_species_of_genus",
    "gtdb_taxonomy",
    "checkm2_completeness",
    "checkm2_contamination",
    "protein_count",
]

NUMERIC_COLUMNS = [
    "checkm2_completeness",
    "checkm2_contamination",
    "protein_count",
]

DOWNLOAD_DIR = Path("gtdb_downloads")
TMP_PROTEOME_DIR = Path("./tmp")
COMBINED_METADATA_FILE = Path("gtdb_selected_metadata.tsv")
SELECTED_REPS_FILE = Path("selected_reps.tsv")
OUTPUT_FASTA_BASENAME = "selected_reps"
GTDB_PROTEIN_DIR = Path(
    "/data/dbs/gtdb/release226/proteins/protein_faa_reps/bacteria/"
)


def download_file(url: str, destination: Path, chunk_size: int = 8192) -> None:
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    handle.write(chunk)


def load_selected_columns_from_gzip(gz_path: Path, source_name: str) -> pd.DataFrame:
    with gzip.open(gz_path, "rt", encoding="utf-8") as handle:
        df = pd.read_csv(
            handle,
            sep="\t",
            usecols=COLUMNS_TO_KEEP,
            low_memory=False,
        )

    df[NUMERIC_COLUMNS] = df[NUMERIC_COLUMNS].apply(pd.to_numeric, errors="coerce")
    df["source"] = source_name
    return df


def safe_delete(path: Path) -> None:
    if path.exists():
        path.unlink()
        print(f"Deleted: {path}")


def add_taxonomy_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["species"] = df["gtdb_taxonomy"].str.extract(r";s__([^;]+)$")[0]
    df["genus"] = df["gtdb_taxonomy"].str.extract(r";g__([^;]+)")[0]
    df["family"] = df["gtdb_taxonomy"].str.extract(r";f__([^;]+)")[0]
    return df


def choose_best_family_fallback(family_df: pd.DataFrame) -> pd.Series | None:
    species_reps = family_df[family_df["gtdb_representative"] == "t"].copy()
    if species_reps.empty:
        return None

    high_quality = species_reps[
        (species_reps["checkm2_completeness"] >= 95)
        & (species_reps["checkm2_contamination"] < 1)
    ]

    ranked_df = high_quality if not high_quality.empty else species_reps
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


def build_selected_reps(df: pd.DataFrame) -> pd.DataFrame:
    genus_reps = df[
        (df["gtdb_type_species_of_genus"] == "t")
        & (df["gtdb_representative"] == "t")
    ].copy()
    genus_reps = genus_reps.drop_duplicates(subset="accession")

    families_with_genus_rep = set(genus_reps["family"].dropna())
    all_families = set(df["family"].dropna())
    families_without_genus_rep = sorted(all_families - families_with_genus_rep)
    print(f"Families without genus rep: {len(families_without_genus_rep):,}")

    fallback_rows = []
    for family in families_without_genus_rep:
        chosen = choose_best_family_fallback(df[df["family"] == family])
        if chosen is not None:
            fallback_rows.append(chosen)

    family_fallback_reps = (
        pd.DataFrame(fallback_rows).drop_duplicates(subset="accession")
        if fallback_rows
        else pd.DataFrame(columns=df.columns)
    )

    selected_reps = pd.concat([genus_reps, family_fallback_reps], ignore_index=True)
    selected_reps = selected_reps.drop_duplicates(subset="accession")
    selected_reps = selected_reps.sort_values(
        by=["family", "genus", "species", "accession"]
    ).reset_index(drop=True)

    return selected_reps


def download_and_build_selected_rep_database(accessions: list[str]) -> None:
    api_key = os.getenv("NCBI_API_KEY")
    downloader = NCBIProteomeDownloader(api_key=api_key)

    TMP_PROTEOME_DIR.mkdir(parents=True, exist_ok=True)

    downloader.download_proteomes(
        accessions=accessions,
        out_dir=str(TMP_PROTEOME_DIR),
        gtdb_dir=str(GTDB_PROTEIN_DIR),
    )

    process_fasta_folder_to_single(
        folder=str(TMP_PROTEOME_DIR),
        output_fasta=f'{OUTPUT_FASTA_BASENAME}.fasta',
        pattern="*.faa",
        line_width=None,
        parallel=False,
    )

    build_mmseqs_db(f"{OUTPUT_FASTA_BASENAME}.fasta", OUTPUT_FASTA_BASENAME)


def main() -> None:
    DOWNLOAD_DIR.mkdir(exist_ok=True)

    all_dfs: list[pd.DataFrame] = []
    downloaded_files: list[Path] = []

    try:
        for source_name, url in URLS.items():
            gz_path = DOWNLOAD_DIR / f"{source_name}_metadata.tsv.gz"

            print(f"Downloading {source_name}...")
            download_file(url, gz_path)
            downloaded_files.append(gz_path)

            print(f"Loading selected columns from {source_name}...")
            all_dfs.append(load_selected_columns_from_gzip(gz_path, source_name))

        data = pd.concat(all_dfs, ignore_index=True)
        data = add_taxonomy_columns(data)

        data[
            COLUMNS_TO_KEEP + ["family", "genus", "species", "source"]
        ].to_csv(COMBINED_METADATA_FILE, sep="\t", index=False)

        print(f"Combined rows: {len(data):,}")
        print(
            f"GTDB species representatives available: "
            f"{(data['gtdb_representative'] == 't').sum():,}"
        )

        selected_reps = build_selected_reps(data)

        selected_family_count = selected_reps["family"].dropna().nunique()
        all_family_count = data["family"].dropna().nunique()
        print(
            f"Families covered by selected reps: "
            f"{selected_family_count:,} / {all_family_count:,}"
        )

        selected_summary = selected_reps[
            ["accession", "gtdb_taxonomy", "protein_count", "source"]
        ].rename(columns={"gtdb_taxonomy": "taxonomy"})

        selected_summary.to_csv(SELECTED_REPS_FILE, sep="\t", index=False)

        print(f"Selected reps: {len(selected_summary):,}")
        print(f"Total protein count: {selected_summary['protein_count'].sum():,}")
        print(f"Saved: {SELECTED_REPS_FILE}")

        accessions = selected_summary["accession"].tolist()
        print(
            f"Downloading/building proteome database for {len(accessions):,} accessions..."
        )
        download_and_build_selected_rep_database(accessions)

    finally:
        print("Cleaning up downloaded GTDB metadata files...")
        for path in downloaded_files:
            safe_delete(path)


if __name__ == "__main__":
    main()
