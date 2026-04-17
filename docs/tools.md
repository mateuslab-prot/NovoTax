# Tools

NovoTax utilises several tools during the pipeline, mainly for the de novo peptide sequencing steps. They are described below and any adaptations made are listed.

## [XuanjiNovo](https://github.com/guomics-lab/MassNet-DDA)
For data-dependent acquisition XuanjiNovo is used.

### Changes
* Docker entrypoint changed to be compatible with Nextflow
* Enforce single GPU use due to bug with multi GPU use on some systems

### Cite
Jun A, Zhang X, et al.  
*MassNet: billion-scale AI-friendly mass spectral corpus enables robust de novo peptide sequencing.*  
bioRxiv. 2025.  
DOI: https://doi.org/10.1101/2025.06.20.660691

## [Cascadia](https://github.com/Noble-Lab/cascadia)
Cascadia utilizes a transformer model to perform de novo sequencing of data-independent acquisition mass spectrometry data.

### Changes
* Adapted for Docker
    * Locked setuptools and Torch to set versions
    * Added Dockerfile
    * Removal of unimod dependency
* Set Torch precision to high to utilise tensor cores for performance boost on newer generation GPUs `set_float32_matmul_precision('high')`

### Cite
Sanders J, Wen B, Rudnick PA, et al.  
*A transformer model for de novo sequencing of data-independent acquisition mass spectrometry data.*  
Nat Methods. 2025;22:1447–1453.  
DOI: https://doi.org/10.1038/s41592-025-02718-y


## [MMseqs2](https://github.com/soedinglab/mmseqs2)
Used for the peptide matching step in Novotax to large proteome databases.

### Cite
Steinegger M, Söding J.  
*MMseqs2 enables sensitive protein sequence searching for the analysis of massive data sets.*  
Nat Biotechnol. 2017;35:1026–1028.  
DOI: https://doi.org/10.1038/nbt.3988

## [GTDB](https://gtdb.ecogenomic.org)
Provides the databases and phylogenetic information used in the peptide matching steps.

### Cite
Parks, D.H., et al.  
*GTDB release 10: a complete and systematic taxonomy for 715 230 bacterial and 17 245 archaeal genomes*  
Nucleic Acids Research, 2025.  
DOI: https://doi.org/10.1093/nar/gkaf1040
