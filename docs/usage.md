# Running NovoTax

## Flags

The base command for running NovoTax is `nextflow run mateuslab-prot/novotax`. To control the input, output and models used, the following flags are available:

**One time flags**  
`-create-dbs PATH` - Creates the GTDB genus database locally at your chosen path. The database size is **~20GB**. 

**Profiles**  
Different profiles exist depending on which system and container platform you're using:  
`-profile apptainer_gpu` **(default)**: Apptainer on Ubuntu using GPU.  
`-profile apptainer_wsl_gpu`: Apptainer on WSL using GPU.  
`-profile docker_gpu`: Docker on Ubuntu/WSL using GPU.

**Mandatory**  
`--input` - Path to .tsv file containing your sample inputs, [see **input** section below](#data-preparation).  
`--output_dir` - Directory that results will be written to.  
`--gtdb_db_dir` - Directory produced by `create-dbs` [containing the GTDB metadata and MMseqs database](installation.md#4-setting-up-novotax).  
`--gtdb_protein_reps` - [Directory containing GTDB representative](installation.md#4-setting-up-novotax) proteome FASTA files (e.g. `protein_faa_reps/`).  

**Optional**  
`--xuanjinovo_model_file PATH` - Path to a XuanjiNovo model file, [see **models** section below](#models).  
`--cascadia_model_file PATH`- Path to a Cascadia model file, [see **models** section below](#models).  
`--filter_contaminants true/false` - Filter [cRAP contaminants](https://www.thegpm.org/crap/) (default **true**). Can be turned off if sample is expected to be of high purity.  
`--filter_host PATH` - Path to fasta file containing host proteome to filter host related peptides (default **NONE**). Can be used if host contaminations are expected.  
`--ncbi_api_key KEY` - [NCBI API key](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/api/api-keys/) to increase rate limits and access to NCBI servers.  
`--genus_score float` - Min. value of genus score for the search iterations to continue (default: **1275**).  
`--max_iterations int` - Max. number of iterations before NovoTax halts (default: **20**).  
`--max_strains int` - Max. number of strains downloaded per species (default: **1000**).  

## Input

NovoTax is designed to accept a list of sample names, file paths and data format using a tab separated (.tsv) file. DDA data to be sequenced using XuanjiNovo is required to be in .mgf format while DIA data to be sequenced with Cascadia requires the data to be in .mzML format. We recommend [msconvert](https://proteowizard.sourceforge.io/tools/msconvert.html) to convert raw data into the appropriate formats.

|      | file_path                                | data_format |
|-----------------|------------------------------------------|-------------|
|  | /full/path/to/folder/demo_xuanjinovo.mgf | dda         |
|    | /full/path/to/folder/demo_cascadia.mzML  | dia         |

## Models
**XuanjiNovo**: The `XuanjiNovo_130M_massnet_massivekb.ckpt` model finetuned on 30M MassiveKB is included in the XuanjiNovo image. A different model can be used with  `--model_file MODEL_FILE_PATH`.

**Cascadia**: The base `Cascadia.ckpt` model is included in the Cascadia image. A different model can be used with `--cascadia_model_file MODEL_FILE_PATH`.

## Output
NovoTax creates one folder for each experiment, creating a folder structure as follows:
```
├── demo_xuanjinovo
│   ├── demo_xuanjinovo_genus_scores.png    - Graph showing the genus scores of all strains found in sample
│   ├── demo_xuanjinovo_peptides.txt        - All peptides in the sample over scoring threshold (0.8 default)
│   ├── demo_xuanjinovo_strains.fasta       - Fasta containing the concatenated proteomes of all strains found
│   └── results.tsv                 - Extended NovoTax output
├── demo_cascadia
│   ├── demo_cascadia_genus_scores.png
│   ├── demo_cascadia_peptides.txt
│   ├── demo_cascadia_strains.fasta
│   └── results.tsv
```

## Example
For a more detailed example run and how to interpret the results, please refer to [this example](example.md).

## Tools used in NovoTax
For a more detailed view on the tools used in NovoTax please refer to the [tools section](tools.md).
