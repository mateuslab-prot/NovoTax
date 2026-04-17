# NovoTax: prokaryotic strain identification from mass spectrometry-based proteomics data

Welcome! If you find any issues with this first release, please do not hesitate to open an issue or contact us directly (`dennis.svedberg at umu.se`)

## What is NovoTax?

<img src="assets/images/workflow.png" alt="NovoTax workflow" height="500">

**NovoTax** is a modular pipeline for identifying prokaryotic strains from mass spectrometry-based proteomics data.

The full NovoTax workflow is designed to go from raw proteomics data to taxonomic assignment and a sample-specific protein database for downstream analysis.

## Why use it?

NovoTax is meant to be practical and accessible:

- one sample sheet
- one command to run
- containerized tools for reproducibility
- designed so non-experts can use it with minimal setup

## Pipeline setup

For more detailed instructions, please refer to the documentation:

- [`Intro`](docs/intro.md)
- [`Installation`](docs/installation.md)
- [`Usage`](docs/usage.md)
- [`Example`](docs/example.md)

## Quick start

### 1. What you need

You need:

- **Nextflow**
- **Apptainer** or **Docker**
- a **tab-separated sample sheet**

### 2. Sample sheet format

Create a tab-separated file like this:

| sample_name     | file_path                                | data_format |
|-----------------|------------------------------------------|-------------|
| XuanjiNovo_demo | /full/path/to/folder/demo_xuanjinovo.mgf | dda         |
| Cascadia_demo   | /full/path/to/folder/demo_cascadia.mzML  | dia         |

### 3. Run the pipeline

```bash
nextflow run mateuslab-prot/novotax
```

Or with custom paths:

```bash
nextflow run main.nf \
  --input /path/to/samples.tsv \
  --output_dir /path/to/results \
  --model_file /path/to/model.ckpt
```

## Output
NovoTax creates one folder for each experiment, creating a folder structure as follows:
```
├── experiment1_dda
│   ├── file1
│   │   ├── file1_db.fasta              # Fasta file for all strains found in file
│   │   ├── file1_peptides.txt          # All unique peptides with score over threshold found in file
│   │   ├── file1_xuanjinovo.tsv        # Raw output of de novo predictions for file
│   │   ├── strain_hits.png             # Quality control plots showing strain scoring for file
│   │   └── strain_hits.tsv             # Taxonomy, GTDB accessions and score for each strain found in file
│   ├── file2
│   │   ├── file2_db.fasta
│   │   ├── file2_peptides.txt
│   │   ├── file2_xuanjinovo.tsv
│   │   ├── strain_hits.png
│   │   └── strain_hits.tsv
│   ├── concat_xuanjinovo.tsv           # Concatenated raw output of de novo predictions for experiment
│   ├── experiment1_peptides.txt        # All unique peptides with score over threshold found in experiment
│   ├── experiment1_db.fasta            # Fasta file for all strains found in experiment
│   ├── strain_hits.png                 # Quality control plots showing strain scoring for experiment
│   └── strain_hits.tsv                 # Taxonomy, GTDB accessions and score for each strain found in experiment
└── experiment2_dia
    ├── file3
    │   ├── file3_cascadia.ssl          # Raw output of de novo predictions for file
    │   ├── file3_db.fasta
    │   ├── strain_hits.png
    │   └── strain_hits.tsv
    ├── concat_cascadia.ssl             # Concatenated raw output of de novo predictions for experiment
    ├── experiment2_peptides.txt
    ├── experiment2_db.fasta
    ├── strain_hits.png
    └── strain_hits.tsv
```


## Cite

If you use **NovoTax**, please cite the tools that make this possible:

**NovoTax**  
Svedberg D, Mateus A.  
*NovoTax: prokaryotic strain identification from mass spectrometry-based proteomics data.*  
bioRxiv. 2026.  
DOI: https://doi.org/10.64898/2026.04.02.715787

**Cascadia**  
Sanders J, Wen B, Rudnick PA, et al.  
*A transformer model for de novo sequencing of data-independent acquisition mass spectrometry data.*  
Nat Methods. 2025;22:1447–1453.  
DOI: https://doi.org/10.1038/s41592-025-02718-y

**XuanjiNovo**  
Jun A, Zhang X, et al.  
*MassNet: billion-scale AI-friendly mass spectral corpus enables robust de novo peptide sequencing.*  
bioRxiv. 2025.  
DOI: https://doi.org/10.1101/2025.06.20.660691

**MMseqs2**  
Steinegger M, Söding J.  
*MMseqs2 enables sensitive protein sequence searching for the analysis of massive data sets.*  
Nat Biotechnol. 2017;35:1026–1028.  
DOI: https://doi.org/10.1038/nbt.3988

**GTDB**  
Parks, D.H., et al.  
*GTDB release 10: a complete and systematic taxonomy for 715 230 bacterial and 17 245 archaeal genomes*  
Nucleic Acids Research, 2025.  
DOI: https://doi.org/10.1093/nar/gkaf1040
