# Running NovoTax

## Quickstart / Demo
1. Clone the NovoTax repository:
```bash
git clone https://github.com/mateuslab-prot/NovoTax/
```
2. Move into the repository:
```bash
cd NovoTax
```
3. Run NovoTax on the example data using the profile that matches your environment
    - Default (no profile flag): Apptainer on Ubuntu using GPU
    - `-profile apptainer_wsl_gpu`: Apptainer on WSL using GPU
    - `-profile docker_gpu`: Docker on Ubuntu/WSL using GPU
```bash
nextflow run main.nf
```
**Note that the first NovoTax run will take a longer time due to first having to retrieve all the containers. Expect the download to take 10-15 minutes and then the demo files takes roughly ~5 minutes to run on a modern desktop GPU.**
## Retrieving models and databases

### Models
**XuanjiNovo**:The `XuanjiNovo_130M_massnet_massivekb.ckpt` model finetuned on 30M MassiveKB is included in the XuanjiNovo image. A different model can be used with  `--model_file MODEL_FILE_PATH`.

**Cascadia**
The base `Cascadia.ckpt` model is included in the Cascadia image. A different model can be used with `--cascadia_model_file MODEL_FILE_PATH`.

### Databases
TODO: Update Zenodo / LFS DOIs

## Data preparation

NovoTax is made to accept a list of sample names, file paths and data format using a tab separated (.tsv) file. DDA data to be sequenced using XuanjiNovo is required to be in .mgf format while DIA data to be sequenced with Cascadia requires the data to be in .mzML format. We recommend [msconvert](https://proteowizard.sourceforge.io/tools/msconvert.html) to convert raw data into the appropriate formats.

| sample_name     | file_path                                | data_format |
|-----------------|------------------------------------------|-------------|
| XuanjiNovo_demo | /full/path/to/folder/demo_xuanjinovo.mgf | dda         |
| Cascadia_demo   | /full/path/to/folder/demo_cascadia.mzML  | dia         |

## Running NovoTax
```bash
nextflow run novotax --sample-path sample.tsv
```

## Output
NovoTax outputs several files during runtime.
* `$SAMPLE_NAME/$SAMPLE_NAME_cascadia.ssl` - Cascadia predictions.
* `$SAMPLE_NAME/$SAMPLE_NAME_xuanjinovo.tsv`- XuanjiNovo preditions.
* `$SAMPLE_NAME/$SAMPLE_NAME_unique_peptides.txt`- All unique peptides predicted, for Unipept or other downstream analysis.
* `$SAMPLE_NAME/$SAMPLE_NAME_novotax_species.tsv` - GTDB accessions and taxonomy for all species predicted to be in the sample, including a relative score.
* `$SAMPLE_NAME/$SAMPLE_NAME_database.fasta` - Concatenated fasta file for all species predicted by NovoTax to be in the sample for downstream analysis.

## Tools used in NovoTax
For a more detailed view on the tools used in NovoTax please refer to the [tools section](tools.md).
