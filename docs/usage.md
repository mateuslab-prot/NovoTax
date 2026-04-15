# Running NovoTax

## Flags

The base command for running NovoTax is `nextflow run mateuslab-prot/novotax`. To control the input, output and models used, the following flags are available:

**NCBI datasets** reads your [API key] to increase rate limits and access to their data by reading the `NCBI_API_KEY`environment key. If possible, ensure this exists in your environment with `export NCBI_API_KEY='YOUR_KEY'`, preferably putting it into your `.bashrc`or equivalent.

**Profiles**  
Different profiles exist depending on which system and container platform you're using:  
`-profile apptainer_gpu` **(default)**: Apptainer on Ubuntu using GPU.  
`-profile apptainer_wsl_gpu`: Apptainer on WSL using GPU.  
`-profile docker_gpu`: Docker on Ubuntu/WSL using GPU.

**Mandatory**  
`-i / --input` - Path to .tsv file containing your sample inputs, [see **input** section below](#data-preparation).  
`-o / --output_dir` - Directory that results will be written to.  

**One time flags**  
`-create-dbs PATH` - Creates the GTDB genus database locally at your chosen path. The database size is **~20GB**. 

**Optional**  
`--xuanjinovo_model_file PATH` - Path to a XuanjiNovo model file, [see **models** section below](#models).  
`--cascadia_model_file PATH`- Path to a Cascadia model file, [see **models** section below](#models).  
`--contaminants_off` - Ignore [cRAP contaminants](https://www.thegpm.org/crap/) filter step. Can be turned off if sample is expected to be of high purity.  
`--host PATH` - Path to fasta file containing host proteome to filter host related peptides  (default **NONE**). Can be used if host contaminations are expected.  
`--ncbi_api_key KEY` - [NCBI API key](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/api/api-keys/) to increase rate limits and access to NCBI servers.  
`--genus_score float` -  Min. value of genus score for the search iterations to continue (default: **1275**). Can be decreased to include less confident species.  
`--max_iterations int`- Max. number of iterations before NovoTax halts (default: **20**). This value can be increased if a community is expected to have more than 20 strains.  
`--max_strains int`- Max. number of strains downloaded per species. (default: **1000**). Can be increased to get better strain coverage at the cost of increased disk usage and runtime.

## Input

NovoTax is designed to accept a list of sample names, file paths and data format using a tab separated (.tsv) file. DDA data to be sequenced using XuanjiNovo is required to be in .mgf format while DIA data to be sequenced with Cascadia requires the data to be in .mzML format. We recommend [msconvert](https://proteowizard.sourceforge.io/tools/msconvert.html) to convert raw data into the appropriate formats.

| experiment_name     | file_path                                | data_format |
|-----------------|------------------------------------------|-------------|
| XuanjiNovo_demo | /full/path/to/folder/demo_xuanjinovo.mgf | dda         |
| Cascadia_demo   | /full/path/to/folder/demo_cascadia.mzML  | dia         |

## Models
**XuanjiNovo**: The `XuanjiNovo_130M_massnet_massivekb.ckpt` model finetuned on 30M MassiveKB is included in the XuanjiNovo image. A different model can be used with  `--model_file MODEL_FILE_PATH`.

**Cascadia**: The base `Cascadia.ckpt` model is included in the Cascadia image. A different model can be used with `--cascadia_model_file MODEL_FILE_PATH`.

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

## Example
For a more detailed example run and how to interpret the results, please refer to [this example](example.md).

## Tools used in NovoTax
For a more detailed view on the tools used in NovoTax please refer to the [tools section](tools.md).
