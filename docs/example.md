# Example usage

## Data preperation

NovoTax is made to accept a list of sample names, file paths and data format using a tab separated (.tsv) file. DDA data to be sequenced using XuanjiNovo is required to be in .mgf format while DIA data to be sequenced with Cascadia requires the data to be in .mzML format. We recommend [msconvert](https://proteowizard.sourceforge.io/tools/msconvert.html) to convert raw data into the appropriate formats.

| sample_name     | file_path                                | data_format |
|-----------------|------------------------------------------|-------------|
| xuanjinovo_test | /full/path/to/folder/demo_xuanjinovo.mgf | dda         |
| cascadia_test   | /full/path/to/folder/demo_cascadia.mzML  | dia         |

## Running NovoTax

```bash
nextflow run main --sample-path sample.tsv
```
