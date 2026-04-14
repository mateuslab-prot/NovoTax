# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import os
import random
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from NovoTax.dbs.create_db import build_mmseqs_db, process_fasta_folder_to_single, write_fasta
from NovoTax.core.gtdb import GTDB
from NovoTax.core.mmseqs import get_mmseqs_hits, get_scores
from NovoTax.core.mmseqs_search import mmseqs_easy_search
from NovoTax.dbs.ncbi import NCBIProteomeDownloader


DATA_ROOT = Path("/home/desv/manuscripts/denovo/data/PXD010000")
RESULTS_DIR = Path("/home/desv/manuscripts/denovo/results_manuscript")

PEPTIDE_FASTA_DIR = Path("fastas/peptides")
MMSEQS_RESULTS_DIR = Path("mmseqs_results")
TMP_FASTA_DIR = Path("fastas/tmp")
TMP_SPECIES_FASTA_DIR = Path("fastas/tmp_species")

SELECTED_REPS_DB = Path("mmseqs_dbs/selected_reps")
CRAP_DB = Path("mmseqs_dbs/crap")
HOST_DBS = {
    "human": Path("mmseqs_dbs/human"),
}

MMSEQS_DB_DIR = Path("mmseqs_dbs/v2")
GTDB_PROTEIN_DIR = Path("/data/dbs/gtdb/release226/proteins/protein_faa_reps/bacteria/")

MAX_SPECIES_ACCESSIONS = 1000
RNG = random.Random(42)


@dataclass(frozen=True)
class SearchResult:
    result_file: Path
    best_accession: str
    best_score: float
    top_hits: list[tuple[str, float]]
    p_value: float | None
    decoy_mean: float
    decoy_max: float
    n_decoys: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Go from de novo predictions to species / strain ID"
    )
    parser.add_argument(
        "--host",
        help="Host to filter out",
        default=None,
        choices=sorted(HOST_DBS),
    )
    parser.add_argument(
        "--contaminants",
        help="Filter cRAP contaminants",
        action="store_true",
    )
    return parser.parse_args()


def decoy_pvalue(decoys: Iterable[float], real_score: float) -> tuple[float | None, float, float, int]:
    decoys = np.asarray(list(decoys), dtype=float)
    real_score = float(real_score)

    if decoys.size == 0:
        return None, float("nan"), float("nan"), 0

    return (
        float(np.mean(decoys >= real_score)),
        float(np.mean(decoys)),
        float(np.max(decoys)),
        int(decoys.size),
    )


def reset_tmp_dirs() -> None:
    for folder in (TMP_FASTA_DIR, TMP_SPECIES_FASTA_DIR):
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True, exist_ok=True)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def mmseqs_db_exists(db_prefix: Path) -> bool:
    return any(db_prefix.parent.glob(f"{db_prefix.name}*"))


def read_xuanjinovo(path: Path, score_threshold: float = 0.8) -> dict[str, str]:
    peptides: dict[str, str] = {}
    idx = 1

    with path.open() as handle:
        next(handle, None)  # header
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 4:
                continue

            _, prediction, _, score = parts
            if float(score) < score_threshold:
                continue

            peptides[str(idx)] = re.sub(r"\[.*?\]", "", prediction)
            idx += 1

    return peptides

def read_cascadia(path: Path, score_threshold: float = 0.8) -> dict[str, str]:
    peptides: dict[str, str] = {}
    idx = 1

    with path.open() as handle:
        next(handle, None)  # header
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 8:
                continue

            prediction, score = parts[3], float(parts[5])
            if float(score) < score_threshold:
                continue

            peptides[str(idx)] = re.sub(r"\[.*?\]", "", prediction)
            idx += 1

    return peptides

def read_cascadia(file, score_threshold=0.8):
    peptides = dict()
    c = 1
    with open(file) as f:
        header = f.readline()
        for line in f:
            line = line.strip().split("\t")
            peptide = line[3]
            score = float(line[5])
            if score >= score_threshold:
                peptides[str(c)] = peptide
                c += 1
    return peptides

def write_query_fasta(
    peptides: dict[str, str],
    sample_name: str,
    *,
    suffix: str,
    reverse: bool = False,
) -> Path:
    query_fasta = PEPTIDE_FASTA_DIR / f"{sample_name}_{suffix}.fasta"
    ensure_parent(query_fasta)
    write_fasta(peptides, query_fasta, line_width=None, reverse=reverse)
    return query_fasta


def remove_hits_from_peptides(peptides: dict[str, str], result_file: Path) -> int:
    removed = 0
    for hit in set(get_mmseqs_hits(result_file)):
        if peptides.pop(hit, None) is not None:
            removed += 1
    return removed


def run_mmseqs_search(query_fasta: Path, target_db: Path, result_file: Path) -> None:
    ensure_parent(result_file)
    mmseqs_easy_search(
        query_fasta=query_fasta,
        target_db=target_db,
        result_tsv=result_file,
        tmp_dir="tmp",
        e_value=0.001,
    )


def search_and_score(query_fasta: Path, target_db: Path, result_file: Path) -> SearchResult | None:
    run_mmseqs_search(query_fasta, target_db, result_file)

    decoy_scores = get_scores(result_file, reverse=True, normalize=False)
    hit_scores = get_scores(result_file, normalize=False)

    if not hit_scores:
        return None

    adjusted_scores = {
        accession: max(0.0, score - decoy_scores.get(accession, 0.0))
        for accession, score in hit_scores.items()
    }

    if not adjusted_scores:
        return None

    top_hits = sorted(adjusted_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    best_accession, best_score = top_hits[0]
    p_value, decoy_mean, decoy_max, n_decoys = decoy_pvalue(decoy_scores.values(), best_score)

    return SearchResult(
        result_file=result_file,
        best_accession=best_accession,
        best_score=best_score,
        top_hits=top_hits,
        p_value=p_value,
        decoy_mean=decoy_mean,
        decoy_max=decoy_max,
        n_decoys=n_decoys,
    )


def report_search(label: str, result: SearchResult, out) -> None:
    print(
        f"Best {label} hit {result.best_accession} had score {result.best_score}, "
        f"empirical p value {result.p_value} "
        f"(mean decoy score {result.decoy_mean}, max {result.decoy_max})"
    )
    print("Top 10 hits:")

    out.write(f"{label} hits\n")
    for accession, score in result.top_hits:
        print(f"{accession}\t{score}")
        out.write(f"{accession}\t{score}\n")


def filter_against_db(
    peptides: dict[str, str],
    sample_name: str,
    *,
    label: str,
    target_db: Path,
) -> int:
    if not peptides:
        return 0

    print(f"*** Searching {label} and removing hits ***")
    query_fasta = write_query_fasta(peptides, sample_name, suffix="peptides_de_novo")
    result_file = MMSEQS_RESULTS_DIR / f"{sample_name}_{label}.m8"

    run_mmseqs_search(query_fasta, target_db, result_file)
    removed = remove_hits_from_peptides(peptides, result_file)

    print(f"\t*** Removed {removed} {label} peptides ***")
    return removed


def ensure_family_db(
    gtdb: GTDB,
    downloader: NCBIProteomeDownloader,
    family: str,
) -> Path:
    output_fasta = Path(f"fastas/{family}.fasta")
    db_prefix = MMSEQS_DB_DIR / family

    if mmseqs_db_exists(db_prefix):
        return db_prefix

    if not output_fasta.exists():
        family_accessions = gtdb.accessions_from_family(family)
        print(f"*** Downloading {len(family_accessions)} proteomes for family {family} ***")

        downloader.download_proteomes(
            accessions=family_accessions,
            out_dir=str(TMP_FASTA_DIR),
            gtdb_dir=str(GTDB_PROTEIN_DIR),
        )

        process_fasta_folder_to_single(
            folder=TMP_FASTA_DIR,
            output_fasta=output_fasta,
            pattern="*.faa",
            line_width=None,
            parallel=False,
        )

    build_mmseqs_db(output_fasta, db_prefix)
    return db_prefix


def ensure_species_db(
    gtdb: GTDB,
    downloader: NCBIProteomeDownloader,
    species_rep: str,
) -> Path:
    output_fasta = Path(f"fastas/{species_rep}.fasta")
    db_prefix = MMSEQS_DB_DIR / species_rep

    if mmseqs_db_exists(db_prefix):
        return db_prefix

    if not output_fasta.exists():
        species_accessions = gtdb.accessions_from_species_rep(species_rep)
        if len(species_accessions) > MAX_SPECIES_ACCESSIONS:
            species_accessions = RNG.sample(species_accessions, MAX_SPECIES_ACCESSIONS)

        print(
            f"*** Downloading {len(species_accessions)} proteomes "
            f"for species rep {species_rep} ***"
        )

        downloader.download_proteomes(
            accessions=species_accessions,
            out_dir=str(TMP_SPECIES_FASTA_DIR),
            gtdb_dir=str(GTDB_PROTEIN_DIR),
        )

        process_fasta_folder_to_single(
            folder=TMP_SPECIES_FASTA_DIR,
            output_fasta=output_fasta,
            pattern="*.faa",
            line_width=None,
            parallel=False,
        )

    build_mmseqs_db(output_fasta, db_prefix)
    return db_prefix


def remove_best_hit_peptides(peptides: dict[str, str], result_file: Path, best_hit: str) -> int:
    to_remove: set[str] = set()

    with result_file.open() as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue

            peptide, hit = parts[0], parts[1]
            if peptide.startswith("rev_"):
                continue
            if best_hit in hit:
                to_remove.add(peptide)

    for peptide in to_remove:
        peptides.pop(peptide, None)

    return len(to_remove)


def main() -> None:
    args = parse_args()
    data_format = args.data_format.lower()

    gtdb = GTDB()
    downloader = NCBIProteomeDownloader(api_key=args.ncbi_api_key)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PEPTIDE_FASTA_DIR.mkdir(parents=True, exist_ok=True)
    MMSEQS_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if data_format == 'dda':
        files = sorted(DATA_ROOT.glob("*/denovo.tsv"))
    elif data_format == 'dia':
        files = sorted(DATA_ROOT.glob("*/denovo.tsv"))
    for file in files:
        sample_name = file.parent.name
        result_path = RESULTS_DIR / f"{sample_name}.tsv"

        if result_path.exists():
            continue

        reset_tmp_dirs()
        
        if data_format == "dda":
            peptides = read_xuanjinovo(file, score_threshold=0.8)
        elif data_format == "dia":
            peptides = read_cascadia(file, score_threshold=0.8)

        with result_path.open("w") as out:
            out.write(f"peptides\t{len(peptides)}\n")
            print(f"\nWorking on {sample_name}")

            while True:
                print("*** Reading de novo results ***")
                print(f"\t*** Found {len(peptides)} unique peptides ***")

                if not peptides:
                    out.write("No peptides remaining, end of search\n")
                    break

                if args.contaminants:
                    filter_against_db(
                        peptides,
                        sample_name,
                        label="cRAP",
                        target_db=CRAP_DB,
                    )

                if args.host:
                    filter_against_db(
                        peptides,
                        sample_name,
                        label=args.host,
                        target_db=HOST_DBS[args.host],
                    )

                if not peptides:
                    out.write("No peptides remaining after filtering, end of search\n")
                    break

                query_fasta = write_query_fasta(
                    peptides,
                    sample_name,
                    suffix="peptides_filtered",
                    reverse=True,
                )

                print("*** Searching MMseqs2 genus DB ***")
                genus_result = search_and_score(
                    query_fasta,
                    SELECTED_REPS_DB,
                    MMSEQS_RESULTS_DIR / f"{sample_name}_genus.m8",
                )
                if genus_result is None:
                    print("No genus matches found!")
                    out.write("No matches, end of search\n")
                    break
                report_search("genus", genus_result, out)

                best_hit_family = gtdb.metadata.loc[genus_result.best_accession, "family"]
                family_db = ensure_family_db(gtdb, downloader, best_hit_family)

                print("\n*** Searching MMseqs2 family DB ***")
                family_result = search_and_score(
                    query_fasta,
                    family_db,
                    MMSEQS_RESULTS_DIR / f"{sample_name}_{best_hit_family}_family.m8",
                )
                if family_result is None:
                    print("No family matches found!")
                    out.write("No matches, end of search\n")
                    break
                report_search("family", family_result, out)

                best_hit_species = family_result.best_accession
                species_db = ensure_species_db(gtdb, downloader, best_hit_species)

                print("\n*** Searching MMseqs2 strain DB ***")
                strain_result = search_and_score(
                    query_fasta,
                    species_db,
                    MMSEQS_RESULTS_DIR / f"{sample_name}_{best_hit_species}.m8",
                )
                if strain_result is None:
                    print("No strain matches found!")
                    out.write("No matches, end of search\n")
                    break
                report_search("strain", strain_result, out)

                removed = remove_best_hit_peptides(
                    peptides,
                    strain_result.result_file,
                    strain_result.best_accession,
                )
                print(
                    f"Removing {removed} peptides from peptide list that hit "
                    f"{strain_result.best_accession}"
                )
                print(f"{len(peptides)} remain\n")

                out.write(f"removed_peptides\t{removed}\n")
                reset_tmp_dirs()
                

if __name__ == "__main__":
    main()
