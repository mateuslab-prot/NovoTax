#!/usr/bin/env python3

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

log = logging.getLogger(__name__)


@dataclass
class AssemblyTag:
    tag: str
    assembly: str


@dataclass
class ProteomeResult:
    tag: str
    assembly: str
    source: str  # 'gtdb', 'ncbi', 'skipped_existing', 'ncbi_no_data', 'missing', 'error'
    path: Optional[Path] = None
    message: Optional[str] = None


class NCBIProteomeDownloader:

    def __init__(self, datasets_cmd: str = "datasets", api_key: Optional[str] = None):
        self.datasets_cmd = datasets_cmd
        self.api_key = api_key

        if shutil.which(self.datasets_cmd) is None:
            raise RuntimeError(
                f"NCBI Datasets CLI '{self.datasets_cmd}' not found on PATH. "
                "Install it and ensure the 'datasets' command is available."
            )


    def download_proteomes(
        self,
        accessions: Iterable[str],
        out_dir: str | Path,
        batch_size: int = 1000,
        keep_dehydrated_zips: bool = False,
        gtdb_dir: str | Path | None = None,
    ) -> Dict[str, ProteomeResult]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        acc_list: List[str] = [a.strip() for a in accessions if a and a.strip()]
        if not acc_list:
            raise ValueError("No accessions provided.")

        tags: List[AssemblyTag] = [self._normalize_accession(a) for a in acc_list]

        results: Dict[str, ProteomeResult] = {}

        need_ncbi: List[AssemblyTag] = []
        from_gtdb = 0

        if gtdb_dir is not None:
            gtdb_dir = Path(gtdb_dir)
            if not gtdb_dir.is_dir():
                raise ValueError(f"GTDB directory does not exist or is not a directory: {gtdb_dir}")

            for t in tags:
                res = self._try_copy_from_gtdb(t, gtdb_dir, out_dir)
                if res is not None:
                    results[t.tag] = res
                    from_gtdb += 1
                else:
                    need_ncbi.append(t)
        else:
            need_ncbi = tags

        log.info(
            "Total accessions: %d (from GTDB: %d, from NCBI: %d)",
            len(tags),
            from_gtdb,
            len(need_ncbi),
        )

        for i in range(0, len(need_ncbi), batch_size):
            batch = need_ncbi[i : i + batch_size]
            log.info(
                "Processing NCBI batch %d (%d accessions: %s ... %s)",
                (i // batch_size) + 1,
                len(batch),
                batch[0].tag,
                batch[-1].tag,
            )
            batch_results = self._download_batch(
                batch=batch,
                out_dir=out_dir,
                keep_dehydrated_zips=keep_dehydrated_zips,
            )
            for r in batch_results:
                if r.tag not in results or results[r.tag].source == "error":
                    results[r.tag] = r

        return results


    def _normalize_accession(self, acc: str) -> AssemblyTag:
        acc = acc.strip()
        if acc.startswith(("RS_", "GB_")):
            _prefix, rest = acc.split("_", 1)
            return AssemblyTag(tag=acc, assembly=rest)
        else:
            return AssemblyTag(tag=acc, assembly=acc)

    def _try_copy_from_gtdb(self, tag: AssemblyTag, gtdb_dir: Path, out_dir: Path) -> Optional[ProteomeResult]:
        import gzip

        base = tag.tag
        candidates = [
            f"{base}_protein.faa.gz",
            f"{base}_protein.faa",
            f"{base}.faa.gz",
            f"{base}.faa",
        ]

        src: Optional[Path] = None
        gzipped = False

        for name in candidates:
            p = gtdb_dir / name
            if p.exists():
                src = p
                gzipped = p.suffix == ".gz"
                break

        dest = out_dir / f"{tag.tag}.faa"

        if src is None:
            return None

        if dest.exists():
            msg = f"Output already exists for {tag.tag}, skipping GTDB copy."
            log.info(msg + " (%s)", dest)
            return ProteomeResult(
                tag=tag.tag,
                assembly=tag.assembly,
                source="skipped_existing",
                path=dest,
                message=msg,
            )

        if gzipped:
            log.info("Decompressing GTDB proteome for %s from %s to %s", tag.tag, src, dest)
            with gzip.open(src, "rb") as f_in, open(dest, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        else:
            log.info("Copying GTDB proteome for %s from %s to %s", tag.tag, src, dest)
            shutil.copy2(src, dest)

        return ProteomeResult(
            tag=tag.tag,
            assembly=tag.assembly,
            source="gtdb",
            path=dest,
        )

    def _run_datasets(self, args: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        cmd = [self.datasets_cmd] + args
        log.debug("Running command: %s", " ".join(cmd))

        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.stdout:
            log.debug("STDOUT:\n%s", result.stdout)
        if result.stderr:
            log.debug("STDERR:\n%s", result.stderr)

        return result

    def _download_batch(
        self,
        batch: List[AssemblyTag],
        out_dir: Path,
        keep_dehydrated_zips: bool,
    ) -> List[ProteomeResult]:
        results: List[ProteomeResult] = []

        with tempfile.TemporaryDirectory(prefix="ncbi_proteomes_") as tmp:
            tmp_path = Path(tmp)

            acc_file = tmp_path / "accessions.txt"
            acc_file.write_text(
                "\n".join(t.assembly for t in batch) + "\n",
                encoding="utf-8",
            )

            zip_path = tmp_path / "dehydrated.zip"

            dl_args = [
                "download",
                "genome",
                "accession",
                "--inputfile",
                str(acc_file),
                "--include",
                "protein",
                "--dehydrated",
                "--filename",
                str(zip_path),
            ]
            if self.api_key:
                dl_args.extend(["--api-key", self.api_key])

            log.info("Downloading dehydrated batch zip to %s", zip_path)
            dl_proc = self._run_datasets(dl_args)

            if dl_proc.returncode != 0:
                msg = (
                    "NCBI Datasets download failed for batch: "
                    f"exit code {dl_proc.returncode}\nSTDERR:\n{dl_proc.stderr}"
                )
                log.error(msg)
                for t in batch:
                    dest = out_dir / f"{t.tag}.faa"
                    source = "error"
                    if dest.exists():
                        source = "skipped_existing"
                    results.append(
                        ProteomeResult(
                            tag=t.tag,
                            assembly=t.assembly,
                            source=source,
                            path=dest if dest.exists() else None,
                            message=msg,
                        )
                    )
                return results

            unzip_dir = tmp_path / "unzipped"
            unzip_dir.mkdir(parents=True, exist_ok=True)

            log.info("Unzipping dehydrated batch into %s", unzip_dir)
            try:
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(unzip_dir)
            except zipfile.BadZipFile as e:
                msg = f"Dehydrated ZIP appears corrupted: {e}"
                log.error(msg)
                for t in batch:
                    dest = out_dir / f"{t.tag}.faa"
                    results.append(
                        ProteomeResult(
                            tag=t.tag,
                            assembly=t.assembly,
                            source="error",
                            path=dest if dest.exists() else None,
                            message=msg,
                        )
                    )
                return results

            ncbi_dataset_root = unzip_dir / "ncbi_dataset"
            data_dir = ncbi_dataset_root / "data"
            fetch_txt = ncbi_dataset_root / "fetch.txt"

            if not fetch_txt.exists():
                msg = (
                    "NCBI Datasets produced no 'fetch.txt' for this batch. "
                    "Likely no protein sequences ('--include protein') are "
                    "available for these assemblies."
                )
                log.warning(msg)
                for t in batch:
                    dest = out_dir / f"{t.tag}.faa"
                    source = "ncbi_no_data"
                    if dest.exists():
                        source = "skipped_existing"
                    results.append(
                        ProteomeResult(
                            tag=t.tag,
                            assembly=t.assembly,
                            source=source,
                            path=dest if dest.exists() else None,
                            message=msg,
                        )
                    )
                return results

            rh_args = [
                "rehydrate",
                "--directory",
                str(unzip_dir),
            ]
            if self.api_key:
                rh_args.extend(["--api-key", self.api_key])

            log.info("Rehydrating batch in %s", unzip_dir)
            rh_proc = self._run_datasets(rh_args)

            if rh_proc.returncode != 0:
                msg = (
                    "NCBI Datasets rehydrate failed for batch: "
                    f"exit code {rh_proc.returncode}\nSTDERR:\n{rh_proc.stderr}"
                )
                log.error(msg)
                for t in batch:
                    dest = out_dir / f"{t.tag}.faa"
                    source = "error"
                    if dest.exists():
                        source = "ncbi"
                    results.append(
                        ProteomeResult(
                            tag=t.tag,
                            assembly=t.assembly,
                            source=source,
                            path=dest if dest.exists() else None,
                            message=msg,
                        )
                    )
                return results

            if not data_dir.exists():
                msg = (
                    f"Unexpected datasets layout: '{data_dir}' not found. "
                    "Check if the Datasets CLI version or output format has changed."
                )
                log.error(msg)
                for t in batch:
                    dest = out_dir / f"{t.tag}.faa"
                    results.append(
                        ProteomeResult(
                            tag=t.tag,
                            assembly=t.assembly,
                            source="error",
                            path=dest if dest.exists() else None,
                            message=msg,
                        )
                    )
                return results

            for t in batch:
                assembly_dir = data_dir / t.assembly
                dest = out_dir / f"{t.tag}.faa"

                if dest.exists():
                    msg = f"Output already exists for {t.tag}, skipping NCBI copy."
                    log.info(msg + " (%s)", dest)
                    results.append(
                        ProteomeResult(
                            tag=t.tag,
                            assembly=t.assembly,
                            source="skipped_existing",
                            path=dest,
                            message=msg,
                        )
                    )
                    continue

                if not assembly_dir.is_dir():
                    msg = f"No directory found for assembly {t.assembly} in {data_dir}."
                    log.warning(msg)
                    results.append(
                        ProteomeResult(
                            tag=t.tag,
                            assembly=t.assembly,
                            source="missing",
                            path=None,
                            message=msg,
                        )
                    )
                    continue

                protein_faa = assembly_dir / "protein.faa"
                if not protein_faa.exists():
                    msg = f"No protein.faa found for assembly {t.assembly}."
                    log.warning(msg)
                    results.append(
                        ProteomeResult(
                            tag=t.tag,
                            assembly=t.assembly,
                            source="missing",
                            path=None,
                            message=msg,
                        )
                    )
                    continue

                shutil.copy2(protein_faa, dest)
                log.info("Wrote proteome for %s (assembly %s) to %s", t.tag, t.assembly, dest)
                results.append(
                    ProteomeResult(
                        tag=t.tag,
                        assembly=t.assembly,
                        source="ncbi",
                        path=dest,
                    )
                )

            if keep_dehydrated_zips and batch:
                first = batch[0].tag
                last = batch[-1].tag
                dest_zip = out_dir / f"dehydrated_{first}_to_{last}.zip"
                shutil.copy2(zip_path, dest_zip)
                log.info("Saved dehydrated archive to %s", dest_zip)

        return results


def _parse_args(argv=None):
    import argparse

    p = argparse.ArgumentParser(
        description=(
            "Download proteomes from NCBI using Datasets dehydrate/rehydrate, "
            "with optional GTDB shortcut for existing species-rep proteomes."
        )
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-a",
        "--accessions",
        nargs="+",
        help=(
            "Accessions (space-separated). Can be GCF_/GCA_ or GTDB-style "
            "RS_GCF_/GB_GCA_."
        ),
    )
    group.add_argument(
        "-f",
        "--accessions-file",
        help="Path to a text file containing one accession per line.",
    )

    p.add_argument(
        "-o",
        "--out-dir",
        required=True,
        help="Output directory for '<tag>.faa' files.",
    )
    p.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of accessions per NCBI dehydrate/rehydrate batch (default: 1000).",
    )
    p.add_argument(
        "--datasets-cmd",
        default="datasets",
        help="Name or path of the NCBI 'datasets' executable (default: datasets).",
    )
    p.add_argument(
        "--api-key",
        default=None,
        help="NCBI API key (optional; otherwise use NCBI_API_KEY env var).",
    )
    p.add_argument(
        "--keep-dehydrated-zips",
        action="store_true",
        help="Keep dehydrated batch zip archives in the output directory.",
    )
    p.add_argument(
        "--gtdb-dir",
        default=None,
        help=(
            "Directory with GTDB proteomes named like "
            "'GB_GCA_017510985.1_protein.faa.gz'. "
            "If provided, existing GTDB files are used instead of downloading."
        ),
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )

    args = p.parse_args(argv)
    return args


def main(argv=None):
    import sys

    args = _parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if args.accessions:
        accessions = args.accessions
    else:
        accessions = Path(args.accessions_file).read_text(encoding="utf-8").splitlines()

    downloader = NCBIProteomeDownloader(
        datasets_cmd=args.datasets_cmd,
        api_key=args.api_key or os.environ.get("NCBI_API_KEY"),
    )

    results = downloader.download_proteomes(
        accessions=accessions,
        out_dir=args.out_dir,
        batch_size=args.batch_size,
        keep_dehydrated_zips=args.keep_dehydrated_zips,
        gtdb_dir=args.gtdb_dir,
    )

    n_total = len(results)
    n_ok = sum(
        1 for r in results.values()
        if r.source in {"gtdb", "ncbi", "skipped_existing"}
    )
    n_missing = sum(
        1 for r in results.values()
        if r.source in {"missing", "ncbi_no_data"}
    )
    n_error = sum(1 for r in results.values() if r.source == "error")

    log.info(
        "Summary: total=%d, ok=%d, no_data=%d, errors=%d",
        n_total,
        n_ok,
        n_missing,
        n_error,
    )

    if n_error > 0 or n_missing > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
