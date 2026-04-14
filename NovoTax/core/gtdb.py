import pandas as pd
import re

def strip_accession_prefix(accession: str) -> str:
    return re.sub(r'^(RS_|GB_)', '', accession)

class GTDB:
    def __init__(self, data_path='data/bac120_metadata_r226_filtered_columns.tsv'):
        # Read metadata once and store it on the instance
        self.metadata = self._read_metadata(data_path)

    @staticmethod
    def _read_metadata(data_path):
        gtdb_metadata = pd.read_csv(data_path, sep='\t', index_col='accession')
        # Extract family from the taxonomy string
        gtdb_metadata['family'] = gtdb_metadata['gtdb_taxonomy'].str.extract(
            r';f__([^;]+);g__'
        )
        return gtdb_metadata

    def accessions_from_family(self, family: str):
        """
        Return a list of accessions belonging to the given family
        AND where gtdb_representative == 't'.
        """
        mask = (
            (self.metadata['family'] == family) &
            (self.metadata['gtdb_representative'] == 't')
        )
        return self.metadata.index[mask].tolist()

    def accessions_from_species_rep(self, accession: str):
        """
        Return a list of accessions for which the given accession is
        the GTDB genome representative.
        """
        mask = self.metadata['gtdb_genome_representative'] == accession
        return self.metadata.index[mask].tolist()
