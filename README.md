# NovoTax: prokaryotic strain identification from mass spectrometry-based proteomics data

**Dennis Svedberg, André Mateus**  
Department of Chemistry, Umeå University, Umeå, Sweden  
Laboratory for Molecular Infection Medicine Sweden (MIMS), Umeå, Sweden  
Umeå Center for Microbial Research (UCMR), Umeå, Sweden

## What is NovoTax?

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

---

## Cite

If you use **NovoTax**, please cite:

**Svedberg D, Mateus A.**  
*NovoTax: prokaryotic strain identification from mass spectrometry-based proteomics data.*  
bioRxiv (2026).  
DOI: `10.64898/2026.04.02.715787`
