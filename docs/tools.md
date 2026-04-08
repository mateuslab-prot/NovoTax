# Tools

NovoTax utilises several tools during the pipeline, mainly for the de novo peptide sequencing steps. They are described below and any adaptations made are listed.

## [XuanjiNovo](https://github.com/guomics-lab/MassNet-DDA)
For data-dependent acquisition we use XuanjiNovo.

## [Cascadia](https://github.com/Noble-Lab/cascadia)
Cascadia utilises a transformer model to perform de novo sequencing of data-independent acquisition mass spectrometry data.

### Changes
* Adapted for Docker
    * Locked setuptools and Torch to set versions
    * Added Dockerfile
    * Removal of unimod dependency
    * 
* Set Torch precision to high to utilise tensor cores for performance boost on newer generation GPUs `set_float32_matmul_precision('high')`