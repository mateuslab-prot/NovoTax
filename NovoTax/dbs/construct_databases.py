#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import gzip
import os
import shutil
from pathlib import Path

import pandas as pd
import requests

from NovoTax.dbs.create_db import build_mmseqs_db, process_fasta_folder_to_single
from NovoTax.dbs.ncbi import NCBIProteomeDownloader


COLUMNS_TO_KEEP = [
    "accession",
    "gtdb_representative",
    "gtdb_genome_representative",
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

DOWNLOAD_DIRNAME = "_downloads"
TMP_DIRNAME = "_tmp_proteomes"
DEFAULT_GTDB_RELEASE = 226
REQUEST_TIMEOUT_SECONDS = 120


def build_urls(gtdb_release: int) -> dict[str, str]:
    return {
        "bac120": (
            f"https://data.gtdb.aau.ecogenomic.org/releases/"
            f"release{gtdb_release}/{gtdb_release}.0/bac120_metadata_r{gtdb_release}.tsv.gz"
        ),
        "ar53": (
            f"https://data.gtdb.aau.ecogenomic.org/releases/"
            f"release{gtdb_release}/{gtdb_release}.0/ar53_metadata_r{gtdb_release}.tsv.gz"
        ),
    }


def filtered_metadata_filename(gtdb_release: int) -> str:
    return f"GTDB_r{gtdb_release}_filtered_metadata.tsv"


def validate_existing_nonempty_dir(path: Path) -> Path:
    resolved_path = Path(path).expanduser().resolve()

    if not resolved_path.exists():
        raise FileNotFoundError(f"GTDB protein representative directory does not exist: {resolved_path}")
    if not resolved_path.is_dir():
        raise NotADirectoryError(
            f"GTDB protein representative path is not a directory: {resolved_path}"
        )
    if not any(resolved_path.iterdir()):
        raise ValueError(f"GTDB protein representative directory is empty: {resolved_path}")

    return resolved_path


def download_file(url: str, destination: Path, chunk_size: int = 8192) -> None:
    with requests.get(url, stream=True, timeout=REQUEST_TIMEOUT_SECONDS) as response:
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


def safe_rmtree(path: Path) -> None:
    if path.exists():
        print(f"Removing temporary directory: {path}")
        shutil.rmtree(path)


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


def download_and_build_selected_rep_database(
    accessions: list[str],
    tmp_proteome_dir: Path,
    output_dir: Path,
    gtdb_protein_rep_dir: Path,
    gtdb_release: int,
) -> None:
    api_key = os.getenv("NCBI_API_KEY")
    downloader = NCBIProteomeDownloader(api_key=api_key)

    tmp_proteome_dir.mkdir(parents=True, exist_ok=True)

    downloader.download_proteomes(
        accessions=accessions,
        out_dir=str(tmp_proteome_dir),
        gtdb_dir=str(gtdb_protein_rep_dir),
    )

    output_fasta = output_dir / f"GTDB_r{gtdb_release}_extended_genus_reps.fasta"
    output_db = output_dir / f"GTDB_r{gtdb_release}_extended_genus_reps"

    process_fasta_folder_to_single(
        folder=str(tmp_proteome_dir),
        output_fasta=str(output_fasta),
        pattern="*.faa",
        line_width=None,
        parallel=False,
    )

    build_mmseqs_db(str(output_fasta), str(output_db))


def main(
    output_dir: Path,
    gtdb_release: int = DEFAULT_GTDB_RELEASE,
    gtdb_protein_rep_dir: Path | None = None,
) -> None:
    if gtdb_protein_rep_dir is None:
        raise ValueError("gtdb_protein_rep_dir is required")

    output_dir = Path(output_dir).expanduser().resolve()
    gtdb_protein_rep_dir = validate_existing_nonempty_dir(gtdb_protein_rep_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    download_dir = output_dir / DOWNLOAD_DIRNAME
    tmp_proteome_dir = output_dir / TMP_DIRNAME
    filtered_metadata_file = output_dir / filtered_metadata_filename(gtdb_release)
    urls = build_urls(gtdb_release)

    download_dir.mkdir(parents=True, exist_ok=True)

    all_dfs: list[pd.DataFrame] = []
    downloaded_files: list[Path] = []

    try:
        for source_name, url in urls.items():
            gz_path = download_dir / f"{source_name}_metadata.tsv.gz"

            print(f"Downloading {source_name} metadata from {url} ...")
            download_file(url, gz_path)
            downloaded_files.append(gz_path)

            print(f"Loading selected columns from {source_name} metadata ...")
            all_dfs.append(load_selected_columns_from_gzip(gz_path, source_name))

        data = pd.concat(all_dfs, ignore_index=True)
        data[COLUMNS_TO_KEEP].to_csv(filtered_metadata_file, sep="\t", index=False)
        print(f"Saved filtered GTDB metadata: {filtered_metadata_file}")

        data = add_taxonomy_columns(data)

        print(f"Combined rows: {len(data):,}")
        print(
            "GTDB species representatives available: "
            f"{(data['gtdb_representative'] == 't').sum():,}"
        )

        selected_reps = build_selected_reps(data)

        selected_family_count = selected_reps["family"].dropna().nunique()
        all_family_count = data["family"].dropna().nunique()
        print(
            "Families covered by selected reps: "
            f"{selected_family_count:,} / {all_family_count:,}"
        )

        selected_summary = selected_reps[
            ["accession", "gtdb_taxonomy", "protein_count", "source"]
        ]

        print(f"Selected reps: {len(selected_summary):,}")
        print(f"Total protein count: {selected_summary['protein_count'].sum():,}")

        accessions = selected_summary["accession"].tolist()
        print(
            "Downloading/building proteome database for "
            f"{len(accessions):,} accessions ..."
        )
        download_and_build_selected_rep_database(
            accessions=accessions,
            tmp_proteome_dir=tmp_proteome_dir,
            output_dir=output_dir,
            gtdb_protein_rep_dir=gtdb_protein_rep_dir,
            gtdb_release=gtdb_release,
        )
    finally:
        print("Cleaning up downloaded GTDB metadata files ...")
        for path in downloaded_files:
            safe_delete(path)

        safe_rmtree(download_dir)
        safe_rmtree(tmp_proteome_dir)
