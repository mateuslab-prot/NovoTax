# Running NovoTax

## Flags

The base command for running NovoTax is `nextflow run mateuslab-prot/NovoTax`. To control the input, output and models used, the following flags are available:

**One-time database setup**  
`--create_dbs PATH` - Creates the GTDB genus database locally at the chosen path. This mode also requires `--gtdb_protein_reps`. The database size is **~20GB**.  
`--gtdb_release int` - GTDB release used when creating the database (default: **226**).  

**Profiles**  
Apptainer with GPU support is configured by default. The following profiles can be selected explicitly:  
`-profile apptainer_gpu`: Apptainer on Ubuntu using GPU.  
`-profile apptainer_wsl_gpu`: Apptainer on WSL using GPU.  
`-profile docker_gpu`: Docker on Ubuntu/WSL using GPU.

**Mandatory**  
`--input` - Path to the .tsv file containing the sample inputs, [see **input** section below](#input).  
`--gtdb_db_dir` - Directory produced by `--create_dbs`, [containing the GTDB metadata and MMseqs database](installation.md#4-setting-up-novotax).  
`--gtdb_protein_reps` - [Directory containing GTDB representative](installation.md#4-setting-up-novotax) proteome FASTA files (e.g. `protein_faa_reps/`).  

**Optional**  
`--output_dir PATH` - Directory where results will be written (default: **./results**).  
`--xuanjinovo_model_file PATH` - Path to a XuanjiNovo model file, [see **models** section below](#models).  
`--cascadia_model_file PATH` - Path to a Cascadia model file, [see **models** section below](#models).  
`--filter_contaminants true/false` - Filter [cRAP contaminants](https://www.thegpm.org/crap/) (default **true**). Can be turned off if the sample is expected to be of high purity.  
`--filter_host PATH` - Path to a host FASTA file or directory of FASTA files used to filter host-related peptides (default: **NONE**).  
`--ncbi_api_key KEY` - [NCBI API key](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/api/api-keys/) to increase rate limits and access to NCBI servers.  
`--genus_score float` - Min. value of genus score for the search iterations to continue (default: **1275**).  
`--max_iterations int` - Max. number of iterations before NovoTax halts (default: **20**).  
`--max_strains int` - Max. number of strains downloaded per species (default: **1000**).  
`--denovo_score float` - Minimum peptide score to retain for DDA, DIA, and peptide-score inputs. Must be a finite value from 0 to 1 (default: **0.8**).  
`--cache_dir PATH` - Persistent cache for downloaded proteomes, derived MMseqs databases, and reusable search files (default: **.novotax_cache** in the pipeline directory). Cache contents are separated by GTDB release.

## Input

NovoTax accepts a tab-separated (.tsv) sample sheet with `file_path` and
`data_format` columns. Sample names and output folders are derived from each input
filename by taking everything before the first period (for example,
`sample.run.mgf` becomes `sample`). Derived names must be unique, start with a
letter or number, and contain only letters, numbers, periods, underscores, or
hyphens. DDA data sequenced with XuanjiNovo must be in .mgf format, while DIA data
sequenced with Cascadia must be in .mzML format. We recommend
[msconvert](https://proteowizard.sourceforge.io/tools/msconvert.html) for converting
raw data into the appropriate formats.

| file_path                                | data_format |
|------------------------------------------|-------------|
| /full/path/to/folder/demo_xuanjinovo.mgf | dda         |
| /full/path/to/folder/demo_cascadia.mzML  | dia         |
| /full/path/to/folder/sample_peptides.tsv | peptides    |

With `data_format` set to `peptides`, the input bypasses de novo sequencing. The
file must contain exactly two tab-separated fields per nonblank row: peptide
sequence and probability score. A case-insensitive `peptide<TAB>score` header is
optional. Scores must be finite values from 0 to 1; rows at or above
`--denovo_score` are retained. Input order and repeated peptide observations are
preserved. Surrounding whitespace and bracketed annotations are removed from
peptide sequences, and isoleucine (`I`) residues are normalized to leucine (`L`)
for matching.

## Models
**XuanjiNovo**: The `XuanjiNovo_130M_massnet_massivekb.ckpt` model finetuned on 30M MassiveKB is included in the XuanjiNovo image. A different model can be used with `--xuanjinovo_model_file MODEL_FILE_PATH`.

**Cascadia**: The base `Cascadia.ckpt` model is included in the Cascadia image. A different model can be used with `--cascadia_model_file MODEL_FILE_PATH`.

## Output
NovoTax creates one folder per sample:
```
├── demo_xuanjinovo
│   ├── demo_xuanjinovo_genus_scores.png    - Graph showing genus scores across search iterations
│   ├── demo_xuanjinovo_peptides.txt        - Peptides entering the taxonomic search after score and optional cRAP/host filtering
│   ├── demo_xuanjinovo_strains.fasta       - FASTA containing the concatenated proteomes of all selected strains
│   ├── peptide_hits.tsv                    - Provenance and assignment status for peptides entering the taxonomic search
│   └── results.tsv                         - Run settings, timing, search results and summary counts
├── demo_cascadia
│   ├── demo_cascadia_genus_scores.png
│   ├── demo_cascadia_peptides.txt
│   ├── demo_cascadia_strains.fasta
│   ├── peptide_hits.tsv
│   └── results.tsv
```

`peptide_hits.tsv` contains one row for every peptide observation remaining after
the configured cRAP and host filtering. It records the source identifier, original
and searched sequence, input score, and whether the peptide was assigned to a
selected strain. For assigned rows, the MMseqs target and bit score describe the
best supporting hit within that strain; they are provenance fields rather than the
accession score used to select the strain. Repeated peptide observations remain
separate rows. An `unassigned` row was not assigned to a selected strain, but may
still have MMseqs matches. `results.tsv` records run settings, timestamps, top
search hits, iteration summaries, and the total taxonomic input, assigned, and
unassigned peptide-observation counts.

## Example
For a more detailed example run and how to interpret the results, please refer to [this example](example.md).

## Tools used in NovoTax
For a more detailed view on the tools used in NovoTax please refer to the [tools section](tools.md).
