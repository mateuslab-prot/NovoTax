#!/usr/bin/env python3

def get_mmseqs_hits(file_path):
    hits = set()
    with open(file_path) as f:
        for line in f:
            line = line.strip().split('\t')
            query = line[0]
            hits.add(query)
    return hits

def get_scores(file_path, reverse=False, peptides=None, normalize=True):
    scores = {}
    seen = {}
    query_hits = {}

    peptides_set = None
    if peptides is not None:
        peptides_set = {str(p) for p in peptides}

    def use_query(query: str) -> bool:
        is_rev = query.startswith("rev_")

        if reverse:
            if not is_rev:
                return False
        else:
            if is_rev:
                return False

        if peptides_set is not None:
            suffix = query.split("_")[-1]
            if suffix not in peptides_set:
                return False

        return True

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
    scores = {}
    seen = {}
    query_hits = {}

    peptides_set = None
    if peptides is not None:
        peptides_set = {str(p) for p in peptides}

    def use_query(query: str) -> bool:
        is_rev = query.startswith("rev_")

        if reverse:
            if not is_rev:
                return False
        else:
            if is_rev:
                return False

        if peptides_set is not None:
            suffix = query.split("_")[-1]
            if suffix not in peptides_set:
                return False

        return True

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

        if accession not in seen[query]:
            if accession not in scores:
                scores[accession] = 0
            scores[accession] += bitscore / query_hits[query]
            seen[query].add(accession)

    return scores
