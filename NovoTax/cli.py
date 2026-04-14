from __future__ import annotations

import argparse
from pathlib import Path


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

    classify_parser = subparsers.add_parser(
        "classify",
        help="Run classification on the given input file",
    )
    classify_parser.add_argument(
        "filepath",
        type=Path,
        help="Input file to classify",
    )

    return parser


def run_create_dbs(db_path: Path) -> None:
    from NovoTax.dbs.construct_databases import main as construct_databases_main

    db_path = db_path.resolve()
    db_path.mkdir(parents=True, exist_ok=True)

    construct_databases_main(db_path)


# def run_classify(filepath: Path) -> None:
#     from NovoTax.core.classify import main as classify_main

#     filepath = filepath.resolve()
#     if not filepath.exists():
#         raise FileNotFoundError(f"Input file does not exist: {filepath}")

#     classify_main(filepath)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "create-dbs":
        run_create_dbs(args.db_path)
    # elif args.command == "classify":
    #     run_classify(args.filepath)
    else:
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
