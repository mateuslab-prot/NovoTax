nextflow.enable.dsl=2

if( params.model_file != null ) {
    if( !file(params.model_file).exists() ) {
        error "XuanjiNovo model file not found: ${params.model_file}"
    }
}

if( params.cascadia_model_file != null ) {
    if( !file(params.cascadia_model_file).exists() ) {
        error "Cascadia model file not found: ${params.cascadia_model_file}"
    }
}

Channel
    .fromPath(params.samplesheet, checkIfExists: true)
    .splitCsv(header: true, sep: '\t')
    .map { row ->
        def sample_name  = row.sample_name?.toString()?.trim()
        def file_path    = row.file_path?.toString()?.trim()
        def data_format  = row.data_format?.toString()?.trim()?.toLowerCase()

        if( !sample_name || !file_path || !data_format ) {
            error "Each row in samples.tsv must contain sample_name, file_path, and data_format"
        }

        if( !(data_format in ['dda', 'dia']) ) {
            error "Unsupported data_format '${data_format}' for sample '${sample_name}'. Supported values: dda, dia"
        }

        def input_file = file(file_path)
        if( !input_file.exists() ) {
            error "Input file not found for sample '${sample_name}': ${file_path}"
        }

        tuple(sample_name, input_file, data_format)
    }
    .set { samples_ch }

process RUN_XUANJINOVO_WITH_MODEL {
    tag { sample_name }

    publishDir { "${params.outdir}/${sample_name}" }, mode: 'copy'

    input:
    tuple val(sample_name), path(peak_file), val(data_format)
    path model_file

    output:
    tuple val(sample_name), path("${sample_name}_xuanjinovo.tsv"), val(data_format)

    when:
    data_format == 'dda'

    script:
    def peak_name  = peak_file.getName()
    def model_name = model_file.getName()

    """
    set -euo pipefail
    WORKDIR="\$(pwd)"
    OUT_DIR="\$WORKDIR/${sample_name}_xuanjinovo"

    export NUMBA_CACHE_DIR="\$WORKDIR/.numba_cache"
    mkdir -p "\$NUMBA_CACHE_DIR"

    python -m XuanjiNovo.XuanjiNovo \
      --mode=${params.mode} \
      --peak_path="\$WORKDIR/${peak_name}" \
      --model="\$WORKDIR/${model_name}" \
      --output="\$OUT_DIR"

    cp "\$OUT_DIR/denovo.tsv" "\$WORKDIR/${sample_name}_xuanjinovo.tsv"
    """
}

process RUN_XUANJINOVO_DEFAULT_MODEL {
    tag { sample_name }

    publishDir { "${params.outdir}/${sample_name}" }, mode: 'copy'

    input:
    tuple val(sample_name), path(peak_file), val(data_format)

    output:
    tuple val(sample_name), path("${sample_name}_xuanjinovo.tsv"), val(data_format)

    when:
    data_format == 'dda'

    script:
    def peak_name = peak_file.getName()

    """
    set -euo pipefail
    WORKDIR="\$(pwd)"
    OUT_DIR="\$WORKDIR/${sample_name}_xuanjinovo"

    export NUMBA_CACHE_DIR="\$WORKDIR/.numba_cache"
    mkdir -p "\$NUMBA_CACHE_DIR"

    python -m XuanjiNovo.XuanjiNovo \
      --mode=${params.mode} \
      --peak_path="\$WORKDIR/${peak_name}" \
      --model="/opt/models/XuanjiNovo_130M_massnet_massivekb.ckpt" \
      --output="\$OUT_DIR"

    cp "\$OUT_DIR/denovo.tsv" "\$WORKDIR/${sample_name}_xuanjinovo.tsv"
    """
}

process RUN_CASCADIA_WITH_MODEL {
    tag { sample_name }

    publishDir { "${params.outdir}/${sample_name}" }, mode: 'copy'

    input:
    tuple val(sample_name), path(input_file), val(data_format)
    path cascadia_model_file

    output:
    tuple val(sample_name), path("${sample_name}_cascadia.ssl"), val(data_format)

    when:
    data_format == 'dia'

    script:
    def input_name = input_file.getName()
    def model_name = cascadia_model_file.getName()

    """
    set -euo pipefail
    WORKDIR="\$(pwd)"

    cascadia sequence "\$WORKDIR/${input_name}" "\$WORKDIR/${model_name}" -o "\$WORKDIR/${sample_name}_cascadia"
    """
}

process RUN_CASCADIA_DEFAULT_MODEL {
    tag { sample_name }

    publishDir { "${params.outdir}/${sample_name}" }, mode: 'copy'

    input:
    tuple val(sample_name), path(input_file), val(data_format)

    output:
    tuple val(sample_name), path("${sample_name}_cascadia.ssl"), val(data_format)

    when:
    data_format == 'dia'

    script:
    def input_name = input_file.getName()

    """
    set -euo pipefail
    WORKDIR="\$(pwd)"

    cascadia sequence "\$WORKDIR/${input_name}" "/opt/models/cascadia.ckpt" -o "\$WORKDIR/${sample_name}_cascadia"
    """
}

process RUN_NOVOTAX {
    tag { sample_name }

    publishDir { "${params.outdir}/${sample_name}" }, mode: 'copy'

    input:
    tuple val(sample_name), path(result_file), val(data_format)

    output:
    path "${sample_name}_novotax.fasta"

    script:
    def result_name = result_file.getName()

    """
    set -euo pipefail

    python /app/main.py \
      "${sample_name}" \
      "${result_name}" \
      "${data_format}" \
      "${sample_name}_novotax.fasta"
    """
}

workflow {
    dda_samples_ch = samples_ch.filter { sample_name, input_file, data_format ->
        data_format == 'dda'
    }

    xuanjinovo_results = params.model_file != null
        ? RUN_XUANJINOVO_WITH_MODEL(
            dda_samples_ch,
            Channel.value(file(params.model_file))
          )
        : RUN_XUANJINOVO_DEFAULT_MODEL(dda_samples_ch)

    dia_samples_ch = samples_ch.filter { sample_name, input_file, data_format ->
        data_format == 'dia'
    }

    cascadia_results = params.cascadia_model_file != null
        ? RUN_CASCADIA_WITH_MODEL(
            dia_samples_ch,
            Channel.value(file(params.cascadia_model_file))
          )
        : RUN_CASCADIA_DEFAULT_MODEL(dia_samples_ch)

    all_results = xuanjinovo_results.mix(cascadia_results)

    RUN_NOVOTAX(all_results)
}
