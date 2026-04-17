#!/usr/bin/env python3

from __future__ import annotations

import argparse
import inspect
from pathlib import Path


DEFAULT_GTDB_RELEASE = 226


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "t", "1", "yes", "y"}:
        return True
    if normalized in {"false", "f", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("Expected true or false")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("Expected a positive integer")
    return parsed


def existing_dir(value: str) -> Path:
    path = Path(value).expanduser().resolve()

    if not path.exists():
        raise argparse.ArgumentTypeError(f"Directory does not exist: {path}")
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"Expected a directory path: {path}")

    return path


def existing_nonempty_dir(value: str) -> Path:
    path = existing_dir(value)
    if not any(path.iterdir()):
        raise argparse.ArgumentTypeError(f"Directory is empty: {path}")
    return path


def existing_path(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise argparse.ArgumentTypeError(f"Path does not exist: {path}")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="novotax",
        description="NovoTax command-line interface",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    create_dbs_parser = subparsers.add_parser(
        "create-dbs",
        help="Build NovoTax databases in the given directory",
    )
    create_dbs_parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory where NovoTax database files should be written",
    )
    create_dbs_parser.add_argument(
        "--gtdb-protein-reps",
        "--gtdb-protein-rep-dir",
        dest="gtdb_protein_reps",
        type=existing_nonempty_dir,
        required=True,
        help=(
            "Path to the GTDB representative protein FASTA directory. "
            "This directory must exist and must not be empty."
        ),
    )
    create_dbs_parser.add_argument(
        "--gtdb-release",
        type=positive_int,
        default=DEFAULT_GTDB_RELEASE,
        help=f"GTDB release version to use (default: {DEFAULT_GTDB_RELEASE})",
    )

    classify_parser = subparsers.add_parser(
        "classify",
        help="Run classification on the given de novo peptide result file",
    )
    classify_parser.add_argument(
        "filepath",
        type=existing_path,
        help="Input de novo peptide result file to classify",
    )
    classify_parser.add_argument(
        "-o",
        "--output_dir",
        type=Path,
        default=Path("/out"),
        help="Directory where classification results and run artifacts should be written",
    )
    classify_parser.add_argument(
        "--gtdb-db-dir",
        "--gtdb-data-dir",
        dest="gtdb_db_dir",
        type=existing_nonempty_dir,
        required=True,
        help=(
            "Path to the NovoTax GTDB database directory produced by create-dbs. "
            "This directory must exist and must not be empty."
        ),
    )
    classify_parser.add_argument(
        "--gtdb-protein-reps",
        dest="gtdb_protein_reps",
        type=existing_nonempty_dir,
        required=True,
        help=(
            "Path to the GTDB representative protein FASTA directory. "
            "This directory must exist and must not be empty."
        ),
    )
    classify_parser.add_argument(
        "--filter_contaminants",
        type=parse_bool,
        default=True,
        metavar="{true,false}",
        help="If true, run the cRAP contamination filter step (default: true)",
    )
    classify_parser.add_argument(
        "--filter_host",
        type=existing_path,
        default=None,
        help="Path to host FASTA file or directory of FASTA files to build and filter against",
    )
    classify_parser.add_argument(
        "--ncbi_api_key",
        default=None,
        help="NCBI API key for proteome downloading (default: none)",
    )
    classify_parser.add_argument(
        "--genus_score",
        type=float,
        default=1275.0,
        help="Minimum genus score required to continue search iterations (default: 1275)",
    )
    classify_parser.add_argument(
        "--max_iterations",
        type=positive_int,
        default=20,
        help="Maximum number of strain-identification iterations (default: 20)",
    )
    classify_parser.add_argument(
        "--max_strains",
        type=positive_int,
        default=1000,
        help="Maximum number of strains downloaded per species (default: 1000)",
    )

    return parser


def run_create_dbs(
    output_dir: Path,
    gtdb_release: int,
    gtdb_protein_reps: Path,
) -> None:
    from NovoTax.dbs.construct_databases import main as construct_databases_main

    output_dir = output_dir.expanduser().resolve()
    if output_dir.exists() and not output_dir.is_dir():
        raise NotADirectoryError(f"Output path exists and is not a directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    parameters = inspect.signature(construct_databases_main).parameters
    kwargs = {
        "output_dir": output_dir,
        "gtdb_release": gtdb_release,
    }
    if "gtdb_protein_rep_dir" in parameters:
        kwargs["gtdb_protein_rep_dir"] = gtdb_protein_reps
    else:
        kwargs["gtdb_protein_dir"] = gtdb_protein_reps

    construct_databases_main(**kwargs)


def run_classify(
    filepath: Path,
    output_dir: Path,
    gtdb_db_dir: Path,
    gtdb_protein_reps: Path,
    filter_contaminants: bool,
    filter_host: Path | None,
    ncbi_api_key: str | None,
    genus_score: float,
    max_iterations: int,
    max_strains: int,
) -> None:
    from NovoTax.core.classify import main as classify_main

    filepath = filepath.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    gtdb_db_dir = gtdb_db_dir.expanduser().resolve()
    gtdb_protein_reps = gtdb_protein_reps.expanduser().resolve()

    if filter_host is not None:
        filter_host = filter_host.expanduser().resolve()

    output_dir.mkdir(parents=True, exist_ok=True)

    classify_main(
        filepath=filepath,
        output_dir=output_dir,
        gtdb_db_dir=gtdb_db_dir,
        gtdb_protein_reps=gtdb_protein_reps,
        filter_contaminants=filter_contaminants,
        filter_host=filter_host,
        ncbi_api_key=ncbi_api_key,
        genus_score=genus_score,
        max_iterations=max_iterations,
        max_strains=max_strains,
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "create-dbs":
        run_create_dbs(
            output_dir=args.output_dir,
            gtdb_release=args.gtdb_release,
            gtdb_protein_reps=args.gtdb_protein_reps,
        )
        return

    if args.command == "classify":
        run_classify(
            filepath=args.filepath,
            output_dir=args.output_dir,
            gtdb_db_dir=args.gtdb_db_dir,
            gtdb_protein_reps=args.gtdb_protein_reps,
            filter_contaminants=args.filter_contaminants,
            filter_host=args.filter_host,
            ncbi_api_key=args.ncbi_api_key,
            genus_score=args.genus_score,
            max_iterations=args.max_iterations,
            max_strains=args.max_strains,
        )
        return

    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
