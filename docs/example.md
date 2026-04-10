# Running NovoTax

The base command for running NovoTax is `nextflow run mateuslab-prot/novotax`. To control the input, output and models used, the following flags are available:

**Mandatory**  
`-i / --input` - Path to .tsv file containing your sample inputs, [see **input** section below](#data-preparation)  
`-o / --output_dir` - Directory that results will be written to  

**Optional**  
`--xuanjinovo_model_file` - Path to a XuanjiNovo model file, [see **models** section below](#models)  
`--cascadia_model_file`- Path to a Cascadia model file, [see **models** section below](#models)

## Input

NovoTax is made to accept a list of sample names, file paths and data format using a tab separated (.tsv) file. DDA data to be sequenced using XuanjiNovo is required to be in .mgf format while DIA data to be sequenced with Cascadia requires the data to be in .mzML format. We recommend [msconvert](https://proteowizard.sourceforge.io/tools/msconvert.html) to convert raw data into the appropriate formats.

| sample_name     | file_path                                | data_format |
|-----------------|------------------------------------------|-------------|
| XuanjiNovo_demo | /full/path/to/folder/demo_xuanjinovo.mgf | dda         |
| Cascadia_demo   | /full/path/to/folder/demo_cascadia.mzML  | dia         |

## Models
**XuanjiNovo**: The `XuanjiNovo_130M_massnet_massivekb.ckpt` model finetuned on 30M MassiveKB is included in the XuanjiNovo image. A different model can be used with  `--model_file MODEL_FILE_PATH`.

**Cascadia**: The base `Cascadia.ckpt` model is included in the Cascadia image. A different model can be used with `--cascadia_model_file MODEL_FILE_PATH`.

## Databases
TODO: Update Zenodo / LFS DOIs

## Output
NovoTax outputs several files during runtime.
* `$SAMPLE_NAME/$SAMPLE_NAME_cascadia.ssl` - Cascadia predictions.
* `$SAMPLE_NAME/$SAMPLE_NAME_xuanjinovo.tsv`- XuanjiNovo preditions.
* `$SAMPLE_NAME/$SAMPLE_NAME_unique_peptides.txt`- All unique peptides predicted, for Unipept or other downstream analysis.
* `$SAMPLE_NAME/$SAMPLE_NAME_novotax_species.tsv` - GTDB accessions and taxonomy for all species predicted to be in the sample, including a relative score.
* `$SAMPLE_NAME/$SAMPLE_NAME_database.fasta` - Concatenated fasta file for all species predicted by NovoTax to be in the sample for downstream analysis.

## Tools used in NovoTax
For a more detailed view on the tools used in NovoTax please refer to the [tools section](tools.md).
