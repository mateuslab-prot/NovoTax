# Example usage

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
    - Default (no profile flag): Ubuntu GPU
    - `-profile apptainer_wsl_gpu`: Apptainer WSL GPU
    - `-profile docker_gpu`: Docker GPU for Ubuntu/WSL
```bash
nextflow run main.nf
```
## Retrieving models and databases

### Models
I moved these into the container images but can still explain the different ones available for completion.

### Databases
Zenodo? LFS?

## Data preparation

NovoTax is made to accept a list of sample names, file paths and data format using a tab separated (.tsv) file. DDA data to be sequenced using XuanjiNovo is required to be in .mgf format while DIA data to be sequenced with Cascadia requires the data to be in .mzML format. We recommend [msconvert](https://proteowizard.sourceforge.io/tools/msconvert.html) to convert raw data into the appropriate formats.

| sample_name     | file_path                                | data_format |
|-----------------|------------------------------------------|-------------|
| xuanjinovo_test | /full/path/to/folder/demo_xuanjinovo.mgf | dda         |
| cascadia_test   | /full/path/to/folder/demo_cascadia.mzML  | dia         |

## Running NovoTax

```bash
nextflow run main --sample-path sample.tsv
```

For a more detailed view on the tools used in NovoTax please refer to the [tools section](tools.md).