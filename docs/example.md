# Example usage

## Retrieving models and databases

### XuanjiNovo
[XuanjiNovo_130M_massnet_massivekb.ckpt](https://huggingface.co/Wyattz23/XuanjiNovo/resolve/main/XuanjiNovo_130M_massnet_massivekb.ckpt)

### Cascadia
TODO: Upload Cascadia model to non-Google drive location

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