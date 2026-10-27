# NovoTax

NovoTax is a pipeline for **building a compact sample specific protein database** directly from **mass spectrometry-based proteomics data**. Starting from DDA spectra in MGF format or DIA data in mzML format, it performs **de novo peptide sequencing** and maps the resulting peptides to reference proteomes in **GTDB** to find the best matching proteomes. NovoTax is designed as an end-to-end workflow that produces a sample-specific, matching protein database for downstream proteomics analysis.

## What NovoTax does

NovoTax is built for cases where you do not already know which organism is present in the sample, or when you want to investigate whether the sample matches the expected organism and whether additional proteomes are supported.

With the default workflow, NovoTax:

- takes DDA spectra in MGF format or DIA data in mzML format as input
- performs de novo peptide sequencing
- searches those peptides against GTDB
- assigns the closest matching proteome
- can continue on remaining unmatched peptides to detect additional organisms
- provides a protein fasta that can be used for downstream database-based proteomics searches

## Workflow overview

NovoTax consists of three main steps:

### 1. De novo sequencing

By default, NovoTax uses:

- **XuanjiNovo** for DDA data
- **Cascadia** for DIA data

Peptide predictions at or above the confidence threshold are retained for downstream matching. Users can also provide an existing two-column, tab-delimited peptide-and-probability table instead of starting from spectrum files.

### 2. Database peptide matching

NovoTax matches peptides against [**GTDB**](https://gtdb.ecogenomic.org/) using [**MMseqs2**](https://github.com/soedinglab/mmseqs2). To make the search practical on a large reference database, it uses an iterative strategy:

- first a broad search to identify the likely genus
- then a narrower search to identify the likely species
- finally a strain-level search within the identified species

This reduces search space, improves speed, and lowers memory and disk use.

### 3. Proteome selection

NovoTax scores each accession by summing peptide-alignment bitscores and subtracting the corresponding sum for reversed decoy peptides. Negative adjusted scores are set to zero. The best-supported proteome is selected at each step. After proteome assignment, matched peptides are removed, and the remaining peptides are searched again to identify additional organisms in the sample, such as contaminants or other species present in a community.

## What NovoTax is useful for

NovoTax is especially useful when you want to:

- identify the best matching proteome for a given sample
- check whether a sample may be mislabeled
- detect additional species
- generate a more appropriate FASTA for downstream proteomics analysis
- identify the dominant members of a microbial community

## Implementation

NovoTax is implemented as a [**Nextflow**](https://www.nextflow.io) pipeline and packaged with **container images** for its components. In practice, this means the workflow is run through Nextflow, while the individual software components are provided in containers to make installation and execution more reproducible. The pipeline is modular, so users can either run the full default workflow or provide intermediate results.

## Input and output

NovoTax can start from:

- DDA spectra in MGF format
- DIA data in mzML format
- an existing two-column peptide-and-probability table

The main outputs are:

- a list of retained peptide sequences remaining after the configured cRAP, host, and known-proteome filtering
- a provenance table for every peptide observation entering the taxonomic search, including assignment status and, for assigned observations, the best supporting MMseqs2 hit within the selected proteome
- the best matching proteomes in GTDB
- a protein sequence database suitable for downstream proteomics analysis

Users can supply a protein FASTA or directory with `--known_proteomes`. All supplied proteins are included in the final database, and their matching peptides are filtered before searching for additional GTDB proteomes. See [known proteomes](usage.md#known-proteomes).

**To run NovoTax, please first refer to [installation instructions](installation.md).**
