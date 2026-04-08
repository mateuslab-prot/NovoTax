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

---

## Pipeline setup

NovoTax uses:

- **Nextflow** to manage the workflow
- **Docker** to run tools in a reproducible software environment
- a simple **TSV sample sheet** to define input files

This means users do not need to run long Docker commands manually for each sample.

For more detailed instructions, see:

- [`docs/index.md`](docs/index.md)
- [`docs/installation.md`](docs/installation.md)
- [`docs/example.md`](docs/example.md)

---

## Quick start

### 1. What you need

You need:

- **Java**
- **Nextflow**
- **Docker**
- **Docker GPU support**
- **model checkpoint files**
- a **tab-separated sample sheet**

---

### 2. Sample sheet format

Create a tab-separated file like this:

```tsv
sample_name	file_path	type_of_data
sample1	/full/path/to/sample1.mgf	dda
sample2	/full/path/to/sample2.mgf	DDA
```

Notes:
- `type_of_data` expects 'DDA' or 'DIA'

---

### 3. Run the pipeline

```bash
nextflow run main.nf
```

Or with custom paths:

```bash
nextflow run main.nf \
  --samplesheet /path/to/samples.tsv \
  --outdir /path/to/results \
  --model_file /path/to/model.ckpt
```

---

## Installation and notes

Detailed setup instructions and practical notes are available in:

- [`docs/index.md`](docs/index.md)
- [`docs/installation.md`](docs/installation.md)
- [`docs/example.md`](docs/example.md)

These pages cover installation, configuration, and more detailed usage notes.

---

## Output

The pipeline writes one output folder per sample into the output directory.

---

## Resume after a failed run

```bash
nextflow run main.nf -resume
```


## Cite

If you use **NovoTax**, please cite the tools that make this possible:

### NovoTax
Svedberg D, Mateus A.  
*NovoTax: prokaryotic strain identification from mass spectrometry-based proteomics data.*  
bioRxiv. 2026.  
DOI: https://doi.org/10.64898/2026.04.02.715787

### Cascadia
Sanders J, Wen B, Rudnick PA, et al.  
*A transformer model for de novo sequencing of data-independent acquisition mass spectrometry data.*  
Nat Methods. 2025;22:1447–1453.  
DOI: https://doi.org/10.1038/s41592-025-02718-y

### XuanjiNovo
Jun A, Zhang X, et al.  
*MassNet: billion-scale AI-friendly mass spectral corpus enables robust de novo peptide sequencing.*  
bioRxiv. 2025.  
DOI: https://doi.org/10.1101/2025.06.20.660691

### MMseqs2
Steinegger M, Söding J.  
*MMseqs2 enables sensitive protein sequence searching for the analysis of massive data sets.*  
Nat Biotechnol. 2017;35:1026–1028.  
DOI: https://doi.org/10.1038/nbt.3988