#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import os
import random
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import matplotlib.pyplot as plt
import numpy as np

from NovoTax.core.gtdb import GTDB, GTDBAssets, discover_gtdb_assets
from NovoTax.core.mmseqs import get_mmseqs_hits, get_scores
from NovoTax.core.mmseqs_search import mmseqs_easy_search
from NovoTax.dbs.create_db import build_mmseqs_db, process_fasta_folder_to_single, write_fasta
from NovoTax.dbs.ncbi import NCBIProteomeDownloader


DEFAULT_SCORE_THRESHOLD = 0.8
RNG_SEED = 42
DEFAULT_CACHE_ROOT = Path("/tmp/novotax_cache")
NOVOTAX_CACHE_DIR_ENV = "NOVOTAX_CACHE_DIR"
NOVOTAX_CRAP_DB_ENV = "NOVOTAX_CRAP_DB"


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


@dataclass(frozen=True)
class RuntimePaths:
    output_root: Path
    sample_output_dir: Path
    result_path: Path
    peptides_path: Path
    strains_fasta_path: Path
    genus_plot_path: Path
    mmseqs_results_dir: Path
    work_dir: Path
    peptide_fasta_dir: Path
    tmp_fasta_dir: Path
    tmp_species_fasta_dir: Path
    tmp_mmseqs_dir: Path
    tmp_strain_fetch_dir: Path
    cache_root: Path
    fasta_cache_dir: Path
    db_cache_dir: Path
    strain_fasta_cache_dir: Path
    cached_genus_results_dir: Path
    genus_base_result_file: Path


@dataclass(frozen=True)
class ClassificationResources:
    gtdb_assets: GTDBAssets
    gtdb_protein_reps: Path
    crap_db_prefix: Path


def decoy_pvalue(
    decoys: Iterable[float],
    real_score: float,
) -> tuple[float | None, float, float, int]:
    decoys_array = np.asarray(list(decoys), dtype=float)
    real_score = float(real_score)

    if decoys_array.size == 0:
        return None, float("nan"), float("nan"), 0

    return (
        float(np.mean(decoys_array >= real_score)),
        float(np.mean(decoys_array)),
        float(np.max(decoys_array)),
        int(decoys_array.size),
    )


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def ensure_existing_nonempty_dir(path: Path, description: str) -> Path:
    resolved_path = Path(path).expanduser().resolve()

    if not resolved_path.exists():
        raise FileNotFoundError(f"{description} does not exist: {resolved_path}")
    if not resolved_path.is_dir():
        raise NotADirectoryError(f"{description} is not a directory: {resolved_path}")
    if not any(resolved_path.iterdir()):
        raise ValueError(f"{description} is empty: {resolved_path}")

    return resolved_path


def mmseqs_db_exists(db_prefix: Path) -> bool:
    return Path(f"{db_prefix}.dbtype").exists()


def find_crap_db_prefix() -> Path:
    env_value = os.getenv(NOVOTAX_CRAP_DB_ENV)

    candidates = []
    if env_value:
        candidates.append(Path(env_value))

    module_path = Path(__file__).resolve()
    candidates.extend(
        [
            module_path.parents[2] / "assets" / "dbs" / "crap",
            module_path.parents[1] / "assets" / "dbs" / "crap",
        ]
    )

    for candidate in candidates:
        resolved_candidate = candidate.expanduser().resolve()
        if mmseqs_db_exists(resolved_candidate):
            return resolved_candidate

    raise FileNotFoundError(
        "Could not find the bundled cRAP MMseqs database. "
        f"Set {NOVOTAX_CRAP_DB_ENV} or place the DB under assets/dbs/crap."
    )


def resolve_classification_resources(
    gtdb_db_dir: Path,
    gtdb_protein_reps: Path,
) -> ClassificationResources:
    resolved_protein_reps = ensure_existing_nonempty_dir(
        gtdb_protein_reps,
        "GTDB representative protein directory",
    )
    gtdb_assets = discover_gtdb_assets(gtdb_db_dir)
    crap_db_prefix = find_crap_db_prefix()

    return ClassificationResources(
        gtdb_assets=gtdb_assets,
        gtdb_protein_reps=resolved_protein_reps,
        crap_db_prefix=crap_db_prefix,
    )


def reset_tmp_dirs(paths: RuntimePaths) -> None:
    shutil.rmtree(paths.work_dir, ignore_errors=True)

    for folder in (
        paths.peptide_fasta_dir,
        paths.tmp_fasta_dir,
        paths.tmp_species_fasta_dir,
        paths.tmp_mmseqs_dir,
        paths.tmp_strain_fetch_dir,
    ):
        folder.mkdir(parents=True, exist_ok=True)


def cache_root_from_environment() -> Path:
    env_value = os.getenv(NOVOTAX_CACHE_DIR_ENV)
    if env_value:
        return Path(env_value).expanduser().resolve()
    return DEFAULT_CACHE_ROOT


def build_runtime_paths(output_dir: Path, sample_name: str, input_file: Path) -> RuntimePaths:
    output_root = output_dir.expanduser().resolve()
    sample_output_dir = output_root / sample_name

    result_path = sample_output_dir / "results.tsv"
    peptides_path = sample_output_dir / f"{sample_name}_peptides.txt"
    strains_fasta_path = sample_output_dir / f"{sample_name}_strains.fasta"
    genus_plot_path = sample_output_dir / f"{sample_name}_genus_scores.png"

    cache_root = cache_root_from_environment()
    fasta_cache_dir = cache_root / "fastas" / "db_cache"
    db_cache_dir = cache_root / "mmseqs_dbs" / "dynamic"
    strain_fasta_cache_dir = cache_root / "fastas" / "strain_cache"
    cached_genus_results_dir = cache_root / "mmseqs_results" / "genus_base"

    token = hashlib.sha1(str(input_file.resolve()).encode("utf-8")).hexdigest()[:10]
    work_dir = Path("/tmp/novotax_work") / f"{sample_name}_{token}"
    peptide_fasta_dir = work_dir / "fastas" / "peptides"
    tmp_fasta_dir = work_dir / "downloads" / "family"
    tmp_species_fasta_dir = work_dir / "downloads" / "species"
    tmp_mmseqs_dir = work_dir / "mmseqs_tmp"
    tmp_strain_fetch_dir = work_dir / "downloads" / "strain_fetch"
    mmseqs_results_dir = work_dir / "mmseqs_results"

    genus_base_result_file = cached_genus_results_dir / f"{sample_name}_{token}_genus_base.m8"

    for folder in (
        sample_output_dir,
        fasta_cache_dir,
        db_cache_dir,
        strain_fasta_cache_dir,
        cached_genus_results_dir,
    ):
        folder.mkdir(parents=True, exist_ok=True)

    return RuntimePaths(
        output_root=output_root,
        sample_output_dir=sample_output_dir,
        result_path=result_path,
        peptides_path=peptides_path,
        strains_fasta_path=strains_fasta_path,
        genus_plot_path=genus_plot_path,
        mmseqs_results_dir=mmseqs_results_dir,
        work_dir=work_dir,
        peptide_fasta_dir=peptide_fasta_dir,
        tmp_fasta_dir=tmp_fasta_dir,
        tmp_species_fasta_dir=tmp_species_fasta_dir,
        tmp_mmseqs_dir=tmp_mmseqs_dir,
        tmp_strain_fetch_dir=tmp_strain_fetch_dir,
        cache_root=cache_root,
        fasta_cache_dir=fasta_cache_dir,
        db_cache_dir=db_cache_dir,
        strain_fasta_cache_dir=strain_fasta_cache_dir,
        cached_genus_results_dir=cached_genus_results_dir,
        genus_base_result_file=genus_base_result_file,
    )


def cleanup_work_dir(paths: RuntimePaths) -> None:
    shutil.rmtree(paths.work_dir, ignore_errors=True)


def clean_prediction(sequence: str) -> str:
    return re.sub(r"\[.*?\]", "", sequence)


def read_xuanjinovo(path: Path, score_threshold: float = DEFAULT_SCORE_THRESHOLD) -> dict[str, str]:
    peptides: dict[str, str] = {}
    idx = 1

    with path.open() as handle:
        next(handle, None)
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 4:
                continue

            _, prediction, _, score = parts
            if float(score) < score_threshold:
                continue

            peptides[str(idx)] = clean_prediction(prediction)
            idx += 1

    return peptides


def read_cascadia(path: Path, score_threshold: float = DEFAULT_SCORE_THRESHOLD) -> dict[str, str]:
    peptides: dict[str, str] = {}
    idx = 1

    with path.open() as handle:
        next(handle, None)
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 6:
                continue

            prediction = parts[3]
            score = float(parts[5])
            if score < score_threshold:
                continue

            peptides[str(idx)] = clean_prediction(prediction)
            idx += 1

    return peptides


def detect_input_format(path: Path) -> str:
    with path.open() as handle:
        next(handle, None)
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if not parts or all(not field for field in parts):
                continue
            if len(parts) == 4:
                return "xuanjinovo"
            if len(parts) >= 6:
                return "cascadia"

    raise ValueError(
        f"Could not infer input format for {path}. Expected XuanjiNovo-style (4 columns) "
        "or Cascadia-style (>=6 columns) rows."
    )


def get_reader_for_file(path: Path) -> tuple[str, Callable[[Path, float], dict[str, str]]]:
    data_format = detect_input_format(path)
    if data_format == "xuanjinovo":
        return data_format, read_xuanjinovo
    if data_format == "cascadia":
        return data_format, read_cascadia
    raise ValueError(f"Unsupported data format: {data_format}")


def sample_name_from_path(filepath: Path) -> str:
    if filepath.name == "denovo.tsv":
        return filepath.parent.name
    return filepath.stem


def peptide_sort_key(item: tuple[str, str]) -> tuple[int, str]:
    peptide_id, _ = item
    if peptide_id.isdigit():
        return (0, f"{int(peptide_id):012d}")
    return (1, peptide_id)


def write_peptide_list(peptides: dict[str, str], output_path: Path) -> None:
    ensure_parent(output_path)
    with output_path.open("w") as handle:
        for _, peptide in sorted(peptides.items(), key=peptide_sort_key):
            handle.write(f"{peptide}\n")


def ensure_accession_fasta(
    accession: str,
    downloader: NCBIProteomeDownloader,
    paths: RuntimePaths,
    gtdb_protein_reps: Path,
) -> Path:
    cached_fasta = paths.strain_fasta_cache_dir / f"{accession}.faa"
    if cached_fasta.exists():
        return cached_fasta

    paths.tmp_strain_fetch_dir.mkdir(parents=True, exist_ok=True)
    before = set(paths.tmp_strain_fetch_dir.glob("*.faa"))

    downloader.download_proteomes(
        accessions=[accession],
        out_dir=str(paths.tmp_strain_fetch_dir),
        gtdb_dir=str(gtdb_protein_reps),
    )

    after = set(paths.tmp_strain_fetch_dir.glob("*.faa"))
    candidates = sorted(after - before)

    if not candidates:
        candidates = sorted(
            path for path in after if accession in path.name or accession in path.stem
        )

    if not candidates and len(after) == 1:
        candidates = sorted(after)

    if len(candidates) != 1:
        raise RuntimeError(
            f"Could not uniquely resolve FASTA for accession {accession} "
            f"in {paths.tmp_strain_fetch_dir}"
        )

    shutil.copyfile(candidates[0], cached_fasta)
    return cached_fasta


def write_concatenated_strains_fasta(
    accessions: list[str],
    downloader: NCBIProteomeDownloader,
    paths: RuntimePaths,
    gtdb_protein_reps: Path,
) -> None:
    ensure_parent(paths.strains_fasta_path)

    seen: set[str] = set()
    ordered_accessions: list[str] = []
    for accession in accessions:
        if accession not in seen:
            seen.add(accession)
            ordered_accessions.append(accession)

    with paths.strains_fasta_path.open("w") as out_handle:
        for index, accession in enumerate(ordered_accessions):
            fasta_path = ensure_accession_fasta(
                accession=accession,
                downloader=downloader,
                paths=paths,
                gtdb_protein_reps=gtdb_protein_reps,
            )
            with fasta_path.open() as in_handle:
                shutil.copyfileobj(in_handle, out_handle)
            if index != len(ordered_accessions) - 1:
                out_handle.write("\n")


def write_genus_score_plot(
    score_points: list[tuple[str, float, bool]],
    threshold: float,
    output_path: Path,
    gtdb: GTDB,
) -> None:
    ensure_parent(output_path)

    plt.figure(figsize=(10, 5.5))

    if not score_points:
        plt.text(0.5, 0.5, "No genus scores to plot", ha="center", va="center")
        plt.axis("off")
    else:
        x_values = list(range(1, len(score_points) + 1))
        y_values = [max(score, 1e-12) for _, score, _ in score_points]

        plt.plot(x_values, y_values, linestyle=":", marker="o")
        plt.axhline(threshold, linestyle="--", linewidth=1)

        for x_value, y_value, (accession, _, accepted) in zip(x_values, y_values, score_points):
            species = gtdb.species_for_accession(accession) or "unknown species"
            suffix = "" if accepted else " (filtered)"
            plt.annotate(
                f"{accession} - {species}{suffix}",
                xy=(x_value, y_value),
                xytext=(6, 4),
                textcoords="offset points",
                fontsize=8,
            )

        plt.yscale("log")
        plt.xlabel("Iteration")
        plt.ylabel("Genus score")
        plt.title("Genus scores for found strains")
        plt.xticks(x_values)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def write_query_fasta(
    peptides: dict[str, str],
    sample_name: str,
    peptide_fasta_dir: Path,
    *,
    suffix: str,
    reverse: bool = False,
) -> Path:
    query_fasta = peptide_fasta_dir / f"{sample_name}_{suffix}.fasta"
    ensure_parent(query_fasta)
    write_fasta(peptides, query_fasta, line_width=None, reverse=reverse)
    return query_fasta


def remove_hits_from_peptides(peptides: dict[str, str], result_file: Path) -> int:
    removed = 0
    for hit in set(get_mmseqs_hits(result_file)):
        if peptides.pop(hit, None) is not None:
            removed += 1
    return removed


def run_mmseqs_search(
    query_fasta: Path,
    target_db: Path,
    result_file: Path,
    tmp_dir: Path,
) -> None:
    ensure_parent(result_file)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    mmseqs_easy_search(
        query_fasta=query_fasta,
        target_db=target_db,
        result_tsv=result_file,
        tmp_dir=str(tmp_dir),
        e_value=0.001,
    )


def score_result_file(result_file: Path) -> SearchResult | None:
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

    top_hits = sorted(adjusted_scores.items(), key=lambda item: item[1], reverse=True)[:10]
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


def normalize_result_query_id(query_id: str) -> str:
    if query_id.startswith("rev_"):
        return query_id[4:]
    return query_id


def subset_result_file_by_peptides(
    source_result_file: Path,
    allowed_peptides: Iterable[str],
    subset_result_file: Path,
) -> Path:
    allowed = set(allowed_peptides)
    ensure_parent(subset_result_file)

    with source_result_file.open() as src, subset_result_file.open("w") as dst:
        for line in src:
            parts = line.rstrip("\n").split("\t")
            if not parts:
                continue

            peptide_id = normalize_result_query_id(parts[0])
            if peptide_id in allowed:
                dst.write(line)

    return subset_result_file


def score_cached_result_for_peptides(
    source_result_file: Path,
    allowed_peptides: Iterable[str],
    subset_result_file: Path,
) -> SearchResult | None:
    subset_result_file_by_peptides(
        source_result_file=source_result_file,
        allowed_peptides=allowed_peptides,
        subset_result_file=subset_result_file,
    )
    return score_result_file(subset_result_file)


def search_and_score(
    query_fasta: Path,
    target_db: Path,
    result_file: Path,
    tmp_dir: Path,
) -> SearchResult | None:
    run_mmseqs_search(query_fasta, target_db, result_file, tmp_dir=tmp_dir)
    return score_result_file(result_file)


def report_search(label: str, result: SearchResult, out_handle) -> None:
    print(f"Best {label} hit {result.best_accession} had score {result.best_score}")
    print("Top 10 hits:")

    out_handle.write(f"{label} hits\n")
    for accession, score in result.top_hits:
        print(f"{accession}\t{score}")
        out_handle.write(f"{accession}\t{score}\n")


def filter_against_db(
    peptides: dict[str, str],
    sample_name: str,
    peptide_fasta_dir: Path,
    mmseqs_results_dir: Path,
    tmp_mmseqs_dir: Path,
    *,
    label: str,
    target_db: Path,
) -> int:
    if not peptides:
        return 0

    print(f"*** Searching {label} and removing hits ***")
    query_fasta = write_query_fasta(
        peptides,
        sample_name,
        peptide_fasta_dir,
        suffix=f"{label}_filter_query",
    )
    result_file = mmseqs_results_dir / f"{sample_name}_{label}.m8"

    run_mmseqs_search(query_fasta, target_db, result_file, tmp_dir=tmp_mmseqs_dir)
    removed = remove_hits_from_peptides(peptides, result_file)

    print(f"\t*** Removed {removed} {label} peptides ***")
    return removed


def ensure_family_db(
    gtdb: GTDB,
    downloader: NCBIProteomeDownloader,
    family: str,
    paths: RuntimePaths,
    gtdb_protein_reps: Path,
) -> Path:
    output_fasta = paths.fasta_cache_dir / f"{family}.fasta"
    db_prefix = paths.db_cache_dir / family

    if mmseqs_db_exists(db_prefix):
        return db_prefix

    if not output_fasta.exists():
        family_accessions = gtdb.accessions_from_family(family)
        print(f"*** Downloading {len(family_accessions)} proteomes for family {family} ***")

        downloader.download_proteomes(
            accessions=family_accessions,
            out_dir=str(paths.tmp_fasta_dir),
            gtdb_dir=str(gtdb_protein_reps),
        )

        process_fasta_folder_to_single(
            folder=str(paths.tmp_fasta_dir),
            output_fasta=str(output_fasta),
            pattern="*.faa",
            line_width=None,
            parallel=False,
        )

    build_mmseqs_db(str(output_fasta), str(db_prefix))
    return db_prefix


def ensure_species_db(
    gtdb: GTDB,
    downloader: NCBIProteomeDownloader,
    species_rep: str,
    max_strains: int,
    paths: RuntimePaths,
    gtdb_protein_reps: Path,
) -> Path:
    output_fasta = paths.fasta_cache_dir / f"{species_rep}_max{max_strains}.fasta"
    db_prefix = paths.db_cache_dir / f"{species_rep}_max{max_strains}"

    if mmseqs_db_exists(db_prefix):
        return db_prefix

    if not output_fasta.exists():
        species_accessions = gtdb.accessions_from_species_rep(species_rep)
        if len(species_accessions) > max_strains:
            rng = random.Random(f"{RNG_SEED}:{species_rep}:{max_strains}")
            species_accessions = rng.sample(species_accessions, max_strains)

        print(
            f"*** Downloading {len(species_accessions)} proteomes "
            f"for species rep {species_rep} ***"
        )

        downloader.download_proteomes(
            accessions=species_accessions,
            out_dir=str(paths.tmp_species_fasta_dir),
            gtdb_dir=str(gtdb_protein_reps),
        )

        process_fasta_folder_to_single(
            folder=str(paths.tmp_species_fasta_dir),
            output_fasta=str(output_fasta),
            pattern="*.faa",
            line_width=None,
            parallel=False,
        )

    build_mmseqs_db(str(output_fasta), str(db_prefix))
    return db_prefix


def short_hash(path: Path) -> str:
    return hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()[:10]


def ensure_host_db(host_path: Path, paths: RuntimePaths) -> Path:
    if not host_path.exists():
        raise FileNotFoundError(f"Host filter path does not exist: {host_path}")

    suffix = short_hash(host_path)
    fasta_name = f"host_filter_{host_path.stem}_{suffix}.fasta"
    db_name = f"host_filter_{host_path.stem}_{suffix}"

    output_fasta = paths.fasta_cache_dir / fasta_name
    db_prefix = paths.db_cache_dir / db_name

    if mmseqs_db_exists(db_prefix):
        return db_prefix

    if not output_fasta.exists():
        if host_path.is_dir():
            process_fasta_folder_to_single(
                folder=str(host_path),
                output_fasta=str(output_fasta),
                pattern="*.fa*",
                line_width=None,
                parallel=False,
            )
        else:
            shutil.copyfile(host_path, output_fasta)

    build_mmseqs_db(str(output_fasta), str(db_prefix))
    return db_prefix


def remove_best_hit_peptides(
    peptides: dict[str, str],
    result_file: Path,
    best_hit: str,
) -> int:
    to_remove: set[str] = set()

    with result_file.open() as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue

            peptide_id, hit = parts[0], parts[1]
            if peptide_id.startswith("rev_"):
                continue
            if best_hit in hit:
                to_remove.add(peptide_id)

    for peptide_id in to_remove:
        peptides.pop(peptide_id, None)

    return len(to_remove)


def main(
    filepath: Path,
    *,
    output_dir: Path = Path("/out"),
    gtdb_db_dir: Path,
    gtdb_protein_reps: Path,
    filter_contaminants: bool = True,
    filter_host: Path | None = None,
    ncbi_api_key: str | None = None,
    genus_score: float = 1275.0,
    max_iterations: int = 20,
    max_strains: int = 1000,
) -> None:
    filepath = filepath.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()

    if not filepath.exists():
        raise FileNotFoundError(f"Input file does not exist: {filepath}")
    if max_iterations < 1:
        raise ValueError("--max_iterations must be >= 1")
    if max_strains < 1:
        raise ValueError("--max_strains must be >= 1")

    resources = resolve_classification_resources(
        gtdb_db_dir=gtdb_db_dir,
        gtdb_protein_reps=gtdb_protein_reps,
    )

    sample_name = sample_name_from_path(filepath)
    paths = build_runtime_paths(output_dir, sample_name, filepath)
    reset_tmp_dirs(paths)

    try:
        data_format, reader = get_reader_for_file(filepath)
        print(f"Detected input format: {data_format}")

        gtdb = GTDB(resources.gtdb_assets.metadata_path)
        downloader = NCBIProteomeDownloader(api_key=ncbi_api_key)
        peptides = reader(filepath, DEFAULT_SCORE_THRESHOLD)

        host_db: Path | None = None
        if filter_host is not None:
            host_db = ensure_host_db(filter_host.resolve(), paths)

        found_strain_accessions: list[str] = []
        genus_score_points: list[tuple[str, float, bool]] = []

        with paths.result_path.open("w") as out_handle:
            out_handle.write(f"sample\t{sample_name}\n")
            out_handle.write(f"input_file\t{filepath}\n")
            out_handle.write(f"data_format\t{data_format}\n")
            out_handle.write(f"peptides\t{len(peptides)}\n")
            out_handle.write(f"gtdb_db_dir\t{resources.gtdb_assets.db_dir}\n")
            out_handle.write(f"gtdb_release\t{resources.gtdb_assets.release}\n")
            out_handle.write(f"gtdb_metadata\t{resources.gtdb_assets.metadata_path}\n")
            out_handle.write(f"gtdb_genus_db\t{resources.gtdb_assets.genus_db_prefix}\n")
            out_handle.write(f"gtdb_protein_reps\t{resources.gtdb_protein_reps}\n")
            out_handle.write(f"filter_contaminants\t{filter_contaminants}\n")
            out_handle.write(f"filter_host\t{filter_host if filter_host is not None else 'NONE'}\n")
            out_handle.write(f"genus_score_threshold\t{genus_score}\n")
            out_handle.write(f"max_iterations\t{max_iterations}\n")
            out_handle.write(f"max_strains\t{max_strains}\n")

            print(f"\nWorking on {sample_name}")
            print(f"*** Found {len(peptides)} peptides ***")

            if filter_contaminants and peptides:
                filter_against_db(
                    peptides=peptides,
                    sample_name=sample_name,
                    peptide_fasta_dir=paths.peptide_fasta_dir,
                    mmseqs_results_dir=paths.mmseqs_results_dir,
                    tmp_mmseqs_dir=paths.tmp_mmseqs_dir,
                    label="cRAP",
                    target_db=resources.crap_db_prefix,
                )

            if host_db is not None and peptides:
                filter_against_db(
                    peptides=peptides,
                    sample_name=sample_name,
                    peptide_fasta_dir=paths.peptide_fasta_dir,
                    mmseqs_results_dir=paths.mmseqs_results_dir,
                    tmp_mmseqs_dir=paths.tmp_mmseqs_dir,
                    label="host",
                    target_db=host_db,
                )

            write_peptide_list(peptides, paths.peptides_path)

            if not peptides:
                out_handle.write("No peptides remaining after one-time filtering, end of search\n")
            else:
                genus_query_fasta = write_query_fasta(
                    peptides,
                    sample_name,
                    paths.peptide_fasta_dir,
                    suffix="peptides_for_genus_base",
                    reverse=True,
                )

                print("*** Searching MMseqs2 genus DB once ***")
                run_mmseqs_search(
                    genus_query_fasta,
                    resources.gtdb_assets.genus_db_prefix,
                    paths.genus_base_result_file,
                    tmp_dir=paths.tmp_mmseqs_dir,
                )

                base_genus_result = score_result_file(paths.genus_base_result_file)
                if base_genus_result is None:
                    print("No genus matches found!")
                    out_handle.write("No genus matches, end of search\n")
                else:
                    for iteration in range(1, max_iterations + 1):
                        print(f"\n=== Iteration {iteration}/{max_iterations} ===")

                        if not peptides:
                            out_handle.write("No peptides remaining, end of search\n")
                            break

                        current_genus_result = score_cached_result_for_peptides(
                            source_result_file=paths.genus_base_result_file,
                            allowed_peptides=peptides.keys(),
                            subset_result_file=(
                                paths.mmseqs_results_dir
                                / f"{sample_name}_iter{iteration}_genus_subset.m8"
                            ),
                        )
                        if current_genus_result is None:
                            print("No remaining genus matches found!")
                            out_handle.write("No remaining genus matches, end of search\n")
                            break

                        report_search("genus", current_genus_result, out_handle)

                        if current_genus_result.best_score < genus_score:
                            genus_score_points.append(
                                (
                                    current_genus_result.best_accession,
                                    current_genus_result.best_score,
                                    False,
                                )
                            )
                            message = (
                                f"Best genus score {current_genus_result.best_score} below threshold "
                                f"{genus_score}, end of search\n"
                            )
                            print(message.strip())
                            out_handle.write(message)
                            break

                        best_hit_family = gtdb.family_for_accession(
                            current_genus_result.best_accession
                        )
                        family_db = ensure_family_db(
                            gtdb=gtdb,
                            downloader=downloader,
                            family=best_hit_family,
                            paths=paths,
                            gtdb_protein_reps=resources.gtdb_protein_reps,
                        )

                        iteration_query_fasta = write_query_fasta(
                            peptides,
                            sample_name,
                            paths.peptide_fasta_dir,
                            suffix=f"peptides_iter_{iteration}",
                            reverse=True,
                        )

                        print("\n*** Searching MMseqs2 family DB ***")
                        family_result = search_and_score(
                            iteration_query_fasta,
                            family_db,
                            paths.mmseqs_results_dir
                            / f"{sample_name}_iter{iteration}_{best_hit_family}_family.m8",
                            tmp_dir=paths.tmp_mmseqs_dir,
                        )
                        if family_result is None:
                            print("No family matches found!")
                            out_handle.write("No family matches, end of search\n")
                            break

                        report_search("family", family_result, out_handle)

                        best_hit_species = family_result.best_accession
                        species_db = ensure_species_db(
                            gtdb=gtdb,
                            downloader=downloader,
                            species_rep=best_hit_species,
                            max_strains=max_strains,
                            paths=paths,
                            gtdb_protein_reps=resources.gtdb_protein_reps,
                        )

                        print("\n*** Searching MMseqs2 strain DB ***")
                        strain_result = search_and_score(
                            iteration_query_fasta,
                            species_db,
                            paths.mmseqs_results_dir
                            / f"{sample_name}_iter{iteration}_{best_hit_species}.m8",
                            tmp_dir=paths.tmp_mmseqs_dir,
                        )
                        if strain_result is None:
                            print("No strain matches found!")
                            out_handle.write("No strain matches, end of search\n")
                            break

                        report_search("strain", strain_result, out_handle)

                        found_strain_accessions.append(strain_result.best_accession)
                        genus_score_points.append(
                            (
                                strain_result.best_accession,
                                current_genus_result.best_score,
                                True,
                            )
                        )

                        removed = remove_best_hit_peptides(
                            peptides,
                            strain_result.result_file,
                            strain_result.best_accession,
                        )
                        print(
                            f"Removing {removed} peptides from peptide list that hit "
                            f"{strain_result.best_accession}"
                        )
                        print(f"{len(peptides)} remain")

                        out_handle.write(f"iteration\t{iteration}\n")
                        out_handle.write(f"removed_peptides\t{removed}\n")

                        reset_tmp_dirs(paths)
                    else:
                        message = f"Reached max_iterations={max_iterations}, end of search\n"
                        print(message.strip())
                        out_handle.write(message)

        write_concatenated_strains_fasta(
            accessions=found_strain_accessions,
            downloader=downloader,
            paths=paths,
            gtdb_protein_reps=resources.gtdb_protein_reps,
        )
        write_genus_score_plot(genus_score_points, genus_score, paths.genus_plot_path, gtdb)
    finally:
        cleanup_work_dir(paths)
