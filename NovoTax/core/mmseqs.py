# -*- coding: utf-8 -*-
"""
Created on Sun Nov 23 23:42:51 2025

@author: densv
"""

def get_mmseqs_hits(file_path):
    hits = set()
    with open(file_path) as f:
        for line in f:
            line = line.strip().split('\t')
            query = line[0]
            hits.add(query)
    return hits

def get_scores(file_path, reverse=False, peptides=None, normalize=True):
    """
    Calculate scores from file_path.

    Parameters
    ----------
    file_path : str
        Path to the input file.
    reverse : bool, optional
        If True, only include queries starting with 'rev_'.
        If False, exclude queries starting with 'rev_'.
    peptides : list[int] or None, optional
        If provided, only include queries whose peptide index (the last
        '_'-separated token in the query) is in this list.

        Examples of valid query formats:
            "peptide_123"
            "rev_peptide_12"

    Returns
    -------
    dict
        Mapping accession -> score.
    """
    scores = {}
    seen = {}
    query_hits = {}

    # Precompute set of allowed peptide IDs as strings
    peptides_set = None
    if peptides is not None:
        peptides_set = {str(p) for p in peptides}

    def use_query(query: str) -> bool:
        """Return True if this query should be included."""
        is_rev = query.startswith("rev_")

        # Reverse / non-reverse filtering
        if reverse:
            if not is_rev:
                return False
        else:
            if is_rev:
                return False

        # Optional peptide filtering
        if peptides_set is not None:
            # Query formats like "peptide_123" or "rev_peptide_123"
            # We just take the last token as the peptide id
            suffix = query.split("_")[-1]
            if suffix not in peptides_set:
                return False

        return True

    # First pass: count hits per query
    with open(file_path) as f:
        for line in f:
            parts = line.strip().split('\t')
            if not parts:
                continue

            query = parts[0]
            if not use_query(query):
                continue

            if query not in query_hits:
                query_hits[query] = 0
            query_hits[query] += 1

    # Second pass: accumulate scores
    with open(file_path) as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 2:
                continue

            query = parts[0]
            if not use_query(query):
                continue

            hit = parts[1]
            bitscore = float(parts[-1])

            accession = "_".join(hit.split("_")[:3])

            if query not in seen:
                seen[query] = set()

            # Only get best bitscore per query and proteome (count accession once per query)
            if accession not in seen[query]:
                if accession not in scores:
                    scores[accession] = 0
                if normalize:
                    scores[accession] += bitscore / query_hits[query]
                else:
                    scores[accession] += bitscore
                seen[query].add(accession)

    return scores

def get_scores_from_list(data_list, reverse=False, peptides=None):
    """
    Calculate scores from file_path.

    Parameters
    ----------
    file_path : str
        Path to the input file.
    reverse : bool, optional
        If True, only include queries starting with 'rev_'.
        If False, exclude queries starting with 'rev_'.
    peptides : list[int] or None, optional
        If provided, only include queries whose peptide index (the last
        '_'-separated token in the query) is in this list.

        Examples of valid query formats:
            "peptide_123"
            "rev_peptide_12"

    Returns
    -------
    dict
        Mapping accession -> score.
    """
    scores = {}
    seen = {}
    query_hits = {}

    # Precompute set of allowed peptide IDs as strings
    peptides_set = None
    if peptides is not None:
        peptides_set = {str(p) for p in peptides}

    def use_query(query: str) -> bool:
        """Return True if this query should be included."""
        is_rev = query.startswith("rev_")

        # Reverse / non-reverse filtering
        if reverse:
            if not is_rev:
                return False
        else:
            if is_rev:
                return False

        # Optional peptide filtering
        if peptides_set is not None:
            # Query formats like "peptide_123" or "rev_peptide_123"
            # We just take the last token as the peptide id
            suffix = query.split("_")[-1]
            if suffix not in peptides_set:
                return False

        return True

    # First pass: count hits per query
    for line in data_list:
        parts = line.strip().split('\t')
        if not parts:
            continue

        query = parts[0]
        if not use_query(query):
            continue

        if query not in query_hits:
            query_hits[query] = 0
        query_hits[query] += 1

    # Second pass: accumulate scores
    for line in data_list:
        parts = line.strip().split('\t')
        if len(parts) < 2:
            continue

        query = parts[0]
        if not use_query(query):
            continue

        hit = parts[1]
        bitscore = float(parts[-1])

        accession = "_".join(hit.split("_")[:3])

        if query not in seen:
            seen[query] = set()

        # Only get best bitscore per query and proteome (count accession once per query)
        if accession not in seen[query]:
            if accession not in scores:
                scores[accession] = 0
            scores[accession] += bitscore / query_hits[query]
            seen[query].add(accession)

    return scores


def get_best_peptides_for_accession(file_path, target_accession):
    current_peptide = False
    current_best = 0
    best_hits = dict()
    peptides_to_remove = []
    with open(file_path) as f:
        for line in f:
            line = line.strip().split('\t')
            peptide = line[0]
            accession = '_'.join(line[1].split('_')[:3])
            bit_score = int(line[-1])

            if peptide != current_peptide:
                current_best = bit_score
                current_peptide = peptide
            if bit_score == current_best:
                if accession == target_accession:
                    peptides_to_remove.append(peptide)
    return peptides_to_remove
