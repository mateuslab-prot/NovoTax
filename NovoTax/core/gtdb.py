#!/usr/bin/env python3

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


METADATA_PATTERN = re.compile(r"^GTDB_r(?P<release>\d+)_filtered_metadata\.tsv$")
GENUS_DB_STEM_TEMPLATE = "GTDB_r{release}_extended_genus_reps"


@dataclass(frozen=True)
class GTDBAssets:
    db_dir: Path
    release: int
    metadata_path: Path
    genus_db_prefix: Path


def strip_accession_prefix(accession: str) -> str:
    return re.sub(r"^(RS_|GB_)", "", accession)


def accession_candidates(accession: str) -> list[str]:
    accession = accession.strip()
    stripped = strip_accession_prefix(accession)

    candidates: list[str] = []
    for candidate in (accession, stripped, f"RS_{stripped}", f"GB_{stripped}"):
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    return candidates


def _mmseqs_db_exists(db_prefix: Path) -> bool:
    return Path(f"{db_prefix}.dbtype").exists()


def discover_gtdb_assets(db_dir: str | Path) -> GTDBAssets:
    resolved_db_dir = Path(db_dir).expanduser().resolve()

    if not resolved_db_dir.exists():
        raise FileNotFoundError(f"GTDB database directory does not exist: {resolved_db_dir}")
    if not resolved_db_dir.is_dir():
        raise NotADirectoryError(f"GTDB database path is not a directory: {resolved_db_dir}")
    if not any(resolved_db_dir.iterdir()):
        raise ValueError(f"GTDB database directory is empty: {resolved_db_dir}")

    metadata_matches: list[tuple[int, Path]] = []
    for path in resolved_db_dir.iterdir():
        match = METADATA_PATTERN.match(path.name)
        if match:
            metadata_matches.append((int(match.group("release")), path))

    if not metadata_matches:
        raise FileNotFoundError(
            "Could not find a GTDB filtered metadata file matching "
            "GTDB_r<release>_filtered_metadata.tsv in "
            f"{resolved_db_dir}"
        )

    releases = {release for release, _ in metadata_matches}
    if len(releases) != 1:
        raise ValueError(
            "Multiple GTDB releases were found in the database directory. "
            "Please keep a single release per directory. Found releases: "
            f"{', '.join(map(str, sorted(releases)))}"
        )

    release, metadata_path = metadata_matches[0]
    genus_db_prefix = resolved_db_dir / GENUS_DB_STEM_TEMPLATE.format(release=release)

    if not _mmseqs_db_exists(genus_db_prefix):
        raise FileNotFoundError(
            "Could not find the GTDB representative MMseqs database for release "
            f"{release} at prefix: {genus_db_prefix}"
        )

    return GTDBAssets(
        db_dir=resolved_db_dir,
        release=release,
        metadata_path=metadata_path,
        genus_db_prefix=genus_db_prefix,
    )


class GTDB:
    def __init__(self, data_path: str | Path) -> None:
        self.metadata = self._read_metadata(data_path)

    @staticmethod
    def _read_metadata(data_path: str | Path) -> pd.DataFrame:
        metadata_path = Path(data_path).expanduser().resolve()
        gtdb_metadata = pd.read_csv(metadata_path, sep="\t", index_col="accession")
        gtdb_metadata["family"] = gtdb_metadata["gtdb_taxonomy"].str.extract(r";f__([^;]+)")
        gtdb_metadata["genus"] = gtdb_metadata["gtdb_taxonomy"].str.extract(r";g__([^;]+)")
        gtdb_metadata["species"] = gtdb_metadata["gtdb_taxonomy"].str.extract(r";s__([^;]+)$")
        return gtdb_metadata

    def resolve_accession(self, accession: str) -> str:
        for candidate in accession_candidates(accession):
            if candidate in self.metadata.index:
                return candidate
        raise KeyError(f"Accession not found in GTDB metadata: {accession}")

    def family_for_accession(self, accession: str) -> str:
        resolved = self.resolve_accession(accession)
        family = self.metadata.at[resolved, "family"]
        if not isinstance(family, str) or not family:
            raise KeyError(f"Family missing for accession: {accession}")
        return family

    def species_for_accession(self, accession: str) -> str | None:
        try:
            resolved = self.resolve_accession(accession)
        except KeyError:
            return None

        species = self.metadata.at[resolved, "species"]
        if isinstance(species, str) and species:
            return species
        return None

    def accessions_from_family(self, family: str) -> list[str]:
        mask = (
            (self.metadata["family"] == family)
            & (self.metadata["gtdb_representative"] == "t")
        )
        return self.metadata.index[mask].tolist()

    def accessions_from_species_rep(self, accession: str) -> list[str]:
        candidates = accession_candidates(accession)
        stripped_candidates = {strip_accession_prefix(candidate) for candidate in candidates}

        mask = self.metadata["gtdb_genome_representative"].isin(candidates)
        if not mask.any():
            representative = self.metadata["gtdb_genome_representative"].astype(str)
            mask = representative.map(strip_accession_prefix).isin(stripped_candidates)

        return self.metadata.index[mask].tolist()
