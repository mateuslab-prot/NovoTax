# NovoTax: prokaryotic strain identification from mass spectrometry-based proteomics data


## Under final revision
Thank you for your interest in NovoTax! We're very excited about releasing the full pipeline as soon as possible and hope to have it out by the end of the week. Check back soon!

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

NovoTax outputs several files during runtime.
* `$SAMPLE_NAME/$SAMPLE_NAME_cascadia.ssl` - Cascadia predictions.
* `$SAMPLE_NAME/$SAMPLE_NAME_xuanjinovo.tsv`- XuanjiNovo preditions.
* `$SAMPLE_NAME/$SAMPLE_NAME_unique_peptides.txt`- All unique peptides predicted, for [Unipept](https://unipept.ugent.be/) or other downstream analysis.
* `$SAMPLE_NAME/$SAMPLE_NAME_novotax_species.tsv` - [GTDB](https://gtdb.ecogenomic.org/) accessions and taxonomy for all species predicted to be in the sample, including a relative score.
* `$SAMPLE_NAME/$SAMPLE_NAME_database.fasta` - Concatenated fasta file for all species predicted by NovoTax to be in the sample for downstream analysis.


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
