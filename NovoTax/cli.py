#!/usr/bin/env python3

from __future__ import annotations

import argparse
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


def existing_nonempty_dir(value: str) -> Path:
    path = Path(value).expanduser().resolve()

    if not path.exists():
        raise argparse.ArgumentTypeError(f"Directory does not exist: {path}")
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"Expected a directory path: {path}")
    if not any(path.iterdir()):
        raise argparse.ArgumentTypeError(f"Directory is empty: {path}")

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
        "--gtdb-protein-rep-dir",
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
        help="Run classification on the given input file",
    )
    classify_parser.add_argument(
        "filepath",
        type=Path,
        help="Input file to classify",
    )
    classify_parser.add_argument(
        "-o",
        "--output_dir",
        type=Path,
        default=Path("/out"),
        help="Directory where classification results and run artifacts should be written",
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
        type=Path,
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
        type=int,
        default=20,
        help="Maximum number of strain-identification iterations (default: 20)",
    )
    classify_parser.add_argument(
        "--max_strains",
        type=int,
        default=1000,
        help="Maximum number of strains downloaded per species (default: 1000)",
    )

    return parser


def run_create_dbs(
    output_dir: Path,
    gtdb_release: int,
    gtdb_protein_rep_dir: Path,
) -> None:
    from NovoTax.dbs.construct_databases import main as construct_databases_main

    output_dir = output_dir.expanduser().resolve()
    if output_dir.exists() and not output_dir.is_dir():
        raise NotADirectoryError(f"Output path exists and is not a directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    construct_databases_main(
        output_dir=output_dir,
        gtdb_release=gtdb_release,
        gtdb_protein_rep_dir=gtdb_protein_rep_dir,
    )


def run_classify(
    filepath: Path,
    output_dir: Path,
    filter_contaminants: bool,
    filter_host: Path | None,
    ncbi_api_key: str | None,
    genus_score: float,
    max_iterations: int,
    max_strains: int,
) -> None:
    from NovoTax.core.classify import main as classify_main

    filepath = filepath.resolve()
    if not filepath.exists():
        raise FileNotFoundError(f"Input file does not exist: {filepath}")

    if filter_host is not None:
        filter_host = filter_host.resolve()
        if not filter_host.exists():
            raise FileNotFoundError(f"Host filter path does not exist: {filter_host}")

    classify_main(
        filepath=filepath,
        output_dir=output_dir,
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
            gtdb_protein_rep_dir=args.gtdb_protein_rep_dir,
        )
        return

    if args.command == "classify":
        run_classify(
            filepath=args.filepath,
            output_dir=args.output_dir,
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
