from __future__ import annotations

import argparse
from pathlib import Path


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "t", "1", "yes", "y"}:
        return True
    if normalized in {"false", "f", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("Expected true or false")


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
        "db_path",
        type=Path,
        help="Directory where databases should be created",
    )
    create_dbs_parser.add_argument(
        "--gtdb-protein-dir",
        type=Path,
        required=False,
        default=Path("/data/dbs/gtdb/release226/proteins/protein_faa_reps/bacteria/"),
        help="Path to GTDB protein directory",
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


def run_create_dbs(db_path: Path, gtdb_protein_dir: Path) -> None:
    from NovoTax.dbs.construct_databases import main as construct_databases_main

    db_path = db_path.resolve()
    db_path.mkdir(parents=True, exist_ok=True)

    construct_databases_main(
        output_dir=db_path,
        gtdb_protein_dir=gtdb_protein_dir,
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
        run_create_dbs(args.db_path, args.gtdb_protein_dir)
    elif args.command == "classify":
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
    else:
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
