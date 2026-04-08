nextflow.enable.dsl=2

if( !file(params.model_file).exists() ) {
    error "XuanjiNovo model file not found: ${params.model_file}"
}

if( !file(params.cascadia_model_file).exists() ) {
    error "Cascadia model file not found: ${params.cascadia_model_file}"
}

Channel
    .fromPath(params.samplesheet, checkIfExists: true)
    .splitCsv(header: true, sep: '\t')
    .map { row ->
        def sample_name  = row.sample_name?.toString()?.trim()
        def file_path    = row.file_path?.toString()?.trim()
        def data_format = row.data_format?.toString()?.trim()?.toLowerCase()

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


process RUN_XUANJINOVO {
    tag { sample_name }

    publishDir params.outdir, mode: 'copy'

    input:
    tuple val(sample_name), path(peak_file), val(data_format)
    path model_file

    output:
    path "${sample_name}_xuanjinovo.tsv"

    when:
    data_format == 'dda'

    script:
    def peak_name  = peak_file.getName()
    def model_name = model_file.getName()

    """
    set -euo pipefail
    WORKDIR="\$(pwd)"
    OUT_DIR="\$WORKDIR/${sample_name}_xuanjinovo"

    python -m XuanjiNovo.XuanjiNovo \
      --mode=${params.mode} \
      --peak_path="\$WORKDIR/${peak_name}" \
      --model="\$WORKDIR/${model_name}" \
      --output="\$OUT_DIR"

    cp "\$OUT_DIR/denovo.tsv" "\$WORKDIR/${sample_name}_xuanjinovo.tsv"
    """
}

process RUN_CASCADIA {
    tag { sample_name }

    publishDir params.outdir, mode: 'copy'

    input:
    tuple val(sample_name), path(input_file), val(data_format)
    path cascadia_model_file

    output:
    path "${sample_name}_cascadia.ssl"

    when:
    data_format == 'dia'

    script:
    def input_name          = input_file.getName()
    def cascadia_model_name = cascadia_model_file.getName()

    """
    WORKDIR="\$(pwd)"

    cascadia sequence "\$WORKDIR/${input_name}" "\$WORKDIR/${cascadia_model_name}" -o "\$WORKDIR/${sample_name}_cascadia"
    """
}

workflow {
    RUN_XUANJINOVO(
        samples_ch,
        Channel.value(file(params.model_file))
    )

    RUN_CASCADIA(
        samples_ch,
        Channel.value(file(params.cascadia_model_file))
    )
}
