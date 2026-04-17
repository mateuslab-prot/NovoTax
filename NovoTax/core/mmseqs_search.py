from __future__ import annotations

from pathlib import Path
import subprocess


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


def mmseqs_easy_search(
    query_fasta: str | Path,
    target_db: str | Path,
    result_tsv: str | Path,
    tmp_dir: str | Path = "tmp",
    mmseqs_bin: str = "mmseqs",
    e_value: float = 1,
) -> Path:
    """
    Run mmseqs easy-search with "your standard" parameters:

        mmseqs easy-search \
            -s 2 --comp-bias-corr 0 --mask 0 -e 1000000 -k 6 \
            --spaced-kmer-pattern 11011101 \
            --seed-sub-mat VTML40.out \
            --gap-open 16 --gap-extend 2 \
            --min-length 9 \
            <query_fasta> <target_db> <result_tsv> <tmp_dir>

    Parameters
    ----------
    query_fasta : path to query peptide FASTA
    target_db   : mmseqs DB prefix (directory/prefix created by createdb)
    result_tsv  : output result file (.m8 / TSV)
    tmp_dir     : directory for mmseqs temporary files (will be created if needed)
    mmseqs_bin  : mmseqs executable (default: "mmseqs")

    Returns
    -------
    Path to the result TSV file.
    """
    query_fasta = Path(query_fasta)
    target_db = Path(target_db)
    result_tsv = Path(result_tsv)
    tmp_dir = Path(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        mmseqs_bin,
        "easy-search",
        str(query_fasta),
        str(target_db),
        str(result_tsv),
        str(tmp_dir),
        "-s", "2",
        "--comp-bias-corr", "0",
        "--mask", "0",
        "-e", str(e_value),
        "-k", "6",
        "--spaced-kmer-pattern", "11011101",
        "--seed-sub-mat", "VTML40.out",
        "--gap-open", "16",
        "--gap-extend", "2",
        "--min-length", "9",
        "--max-seqs", "100000"
    ]

    run_command(cmd)

    return result_tsv
