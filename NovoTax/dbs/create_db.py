from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import subprocess
from typing import Iterator, Tuple

from tqdm import tqdm


# ---------------------------------------------------------------------------
# Existing helpers from your original script (unchanged)
# ---------------------------------------------------------------------------

def run_command(cmd: list[str], cwd: str | Path | None = None) -> subprocess.CompletedProcess:
    """Run a shell command and raise a clear error if it fails."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        return result
    except subprocess.CalledProcessError as e:
        msg = (
            f"Command failed with exit code {e.returncode}\n"
            f"Command: {' '.join(cmd)}\n"
            f"STDOUT:\n{e.stdout}\n"
            f"STDERR:\n{e.stderr}"
        )
        raise RuntimeError(msg) from e


def read_fasta(path: str | Path) -> dict[str, str]:
    """
    Read a FASTA file into a dict: {header_without_>: sequence}.
    Sequences are concatenated into a single string per record.
    """
    path = Path(path)
    sequences: dict[str, str] = {}

    header: str | None = None
    chunks: list[str] = []

    with path.open() as fh:
        for raw_line in tqdm(fh, desc=f"Reading {path.name}"):
            line = raw_line.strip()
            if not line:
                continue  # skip empty lines

            if line.startswith(">"):
                # flush previous record
                if header is not None:
                    sequences[header] = "".join(chunks)
                header = line[1:]  # keep full header (minus '>')
                chunks = []
            else:
                chunks.append(line)

        # flush last record
        if header is not None:
            sequences[header] = "".join(chunks)

    return sequences


def process_proteins(proteins: Mapping[str, str]) -> dict[str, str]:
    """
    Return a new dict with all 'I' replaced by 'L' in each sequence.
    """
    return {name: seq.replace("I", "L") for name, seq in proteins.items()}


def write_fasta(
    proteins: Mapping[str, str],
    path: str | Path,
    line_width: int | None = 60,
    reverse: bool | None = False,
) -> None:
    """
    Write a dict {header: sequence} to a FASTA file.

    By default, wraps sequences at `line_width` characters.
    Set line_width=None to write each sequence as a single line.
    """
    path = Path(path)

    with path.open("w") as out:
        for header, seq in proteins.items():
            out.write(f">{header}\n")

            if line_width is None:
                out.write(seq + "\n")
            else:
                for i in range(0, len(seq), line_width):
                    out.write(seq[i : i + line_width] + "\n")

        if reverse:
            for header, seq in proteins.items():
                out.write(f">rev_{header}\n")

                seq = seq[:-1][::-1] + seq[-1]
                if line_width is None:
                    out.write(seq + "\n")
                else:
                    for i in range(0, len(seq), line_width):
                        out.write(seq[i : i + line_width] + "\n")


def build_mmseqs_db(
    fasta_file: str | Path,
    db_name: str,
    db_dir: str | Path = "",
    mmseqs_bin: str = "mmseqs",
) -> Path:
    """
    Run: mmseqs createdb <fasta_file> <db_dir/db_name>

    Returns the path prefix of the created MMseqs database.
    """
    fasta_file = Path(fasta_file)
    db_dir = Path(db_dir)
    db_dir.mkdir(parents=True, exist_ok=True)

    db_path = db_dir / db_name

    cmd = [
        mmseqs_bin,
        "createdb",
        str(fasta_file),
        str(db_path),
    ]

    run_command(cmd)

    return db_path


# ---------------------------------------------------------------------------
# New streaming FASTA reader & writer helpers
# ---------------------------------------------------------------------------

def iter_fasta_records(path: str | Path) -> Iterator[Tuple[str, str]]:
    """
    Stream FASTA records from a file.

    Yields:
        (header_without_>, sequence_string)
    """
    path = Path(path)
    header: str | None = None
    chunks: list[str] = []

    with path.open() as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith(">"):
                if header is not None:
                    yield header, "".join(chunks)
                header = line[1:]
                chunks = []
            else:
                chunks.append(line)

        if header is not None:
            yield header, "".join(chunks)


def _write_single_record(
    out_handle,
    header: str,
    seq: str,
    line_width: int | None = 60,
) -> None:
    """Write a single FASTA record to an already open handle."""
    out_handle.write(f">{header}\n")
    if line_width is None:
        out_handle.write(seq + "\n")
    else:
        for i in range(0, len(seq), line_width):
            out_handle.write(seq[i : i + line_width] + "\n")


# ---------------------------------------------------------------------------
# Folder → single-output FASTA logic
# ---------------------------------------------------------------------------

def _process_single_file_for_parallel(
    file_path: Path,
) -> list[tuple[str, str]]:
    """
    Helper for parallel mode.

    Reads one FASTA file into memory, applies I->L, renames headers,
    and returns a list of (new_header, seq) tuples.
    """
    ncbi_accession = file_path.stem
    proteins = read_fasta(file_path)
    processed = process_proteins(proteins)

    records: list[tuple[str, str]] = []
    for header, seq in processed.items():
        protein_accession = header.split()[0]
        new_header = f"{ncbi_accession}_{protein_accession}"
        records.append((new_header, seq))
    return records


def process_fasta_folder_to_single(
    folder: str | Path,
    output_fasta: str | Path,
    pattern: str = "*.faa",
    line_width: int | None = None,
    parallel: bool = False,
    workers: int | None = None,
) -> None:
    """
    Process all FASTA files in `folder` matching `pattern` and write them
    into a single FASTA file `output_fasta`.

    For each input file:
        - ncbi_accession is taken from the file stem, e.g. "GCA_017398805.1"
        - protein_accession is the first token of the FASTA header,
          e.g. "MBR5393444.1" from:
              >MBR5393444.1 MAG: hypothetical protein ...

        New header is: f"{ncbi_accession}_{protein_accession}"

    Sequences are processed with process_proteins (I->L).

    Parameters
    ----------
    folder:
        Directory containing *.faa files.
    output_fasta:
        Path to the combined output FASTA file.
    pattern:
        Glob pattern for input files (default: "*.faa").
    line_width:
        Wrap width for sequences (default: None => single-line sequences).
    parallel:
        If True, process files in parallel using multiple processes.
        Note: parallel mode reads each file into memory in one go.
    workers:
        Number of worker processes for parallel mode (default: None =>
        uses ProcessPoolExecutor default).
    """
    folder = Path(folder)
    output_fasta = Path(output_fasta)

    files = sorted(folder.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matching '{pattern}' in {folder}")

    if line_width is None:
        line_width = None  # explicit for clarity

    if not parallel:
        # Pure streaming, very low memory usage (only one record at a time).
        with output_fasta.open("w") as out:
            for file_path in tqdm(files, desc="Processing FASTA files (sequential)"):
                ncbi_accession = file_path.stem

                for header, seq in iter_fasta_records(file_path):
                    protein_accession = header.split()[0]
                    new_header = f"{ncbi_accession}_{protein_accession}"
                    processed_seq = seq.replace("I", "L")
                    _write_single_record(out, new_header, processed_seq, line_width)
    else:
        # Parallel mode: one process per file (or per worker slot).
        # Each worker returns a list of (header, seq); we then stream-write them.
        with output_fasta.open("w") as out:
            with ProcessPoolExecutor(max_workers=workers) as ex:
                futures = {
                    ex.submit(_process_single_file_for_parallel, fp): fp
                    for fp in files
                }

                for fut in tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc="Processing FASTA files (parallel)",
                ):
                    records = fut.result()
                    for header, seq in records:
                        _write_single_record(out, header, seq, line_width)


# ---------------------------------------------------------------------------
# Optional CLI entrypoint (so you can also run it as a script)
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Process a folder of protein FASTA files (*.faa), "
            "rename headers to '{ncbi_accession}_{protein_accession}', "
            "convert I->L, and write a single combined FASTA."
        )
    )
    parser.add_argument("folder", help="Folder containing *.faa files")
    parser.add_argument("output_fasta", help="Output combined FASTA file")
    parser.add_argument(
        "--pattern",
        default="*.faa",
        help="Glob pattern for input files (default: *.faa)",
    )
    parser.add_argument(
        "--line-width",
        type=int,
        default=None,
        help="Wrap sequence lines to this width (default: no wrapping)",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable per-file parallel processing (uses multiple processes)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes for parallel mode (default: executor default)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    process_fasta_folder_to_single(
        folder=args.folder,
        output_fasta=args.output_fasta,
        pattern=args.pattern,
        line_width=args.line_width,
        parallel=args.parallel,
        workers=args.workers,
    )


if __name__ == "__main__":
    main()
