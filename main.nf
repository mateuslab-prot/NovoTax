nextflow.enable.dsl=2

if( !file(params.model_file).exists() ) {
    error "Model file not found: ${params.model_file}"
}

Channel
    .fromPath(params.samplesheet, checkIfExists: true)
    .splitCsv(header: true, sep: '\t')
    .map { row ->
        def sample_name  = row.sample_name?.toString()?.trim()
        def file_path    = row.file_path?.toString()?.trim()
        def type_of_data = row.type_of_data?.toString()?.trim()?.toLowerCase()

        if( !sample_name || !file_path || !type_of_data ) {
            error "Each row in samples.tsv must contain sample_name, file_path, and type_of_data"
        }

        def input_file = file(file_path)
        if( !input_file.exists() ) {
            error "Input file not found for sample '${sample_name}': ${file_path}"
        }

        tuple(sample_name, input_file, type_of_data)
    }
    .set { samples_ch }

process RUN_XUANJINOVO {
    tag { sample_name }

    publishDir params.outdir, mode: 'copy'

    input:
    tuple val(sample_name), path(peak_file), val(type_of_data)
    path model_file

    output:
    path "${sample_name}_xuanjinovo"

    when:
    type_of_data == 'dda'

    script:
    def peak_name  = peak_file.getName()
    def model_name = model_file.getName()

    """
    WORKDIR="\$(pwd)"

    python -m XuanjiNovo.XuanjiNovo \
      --mode=${params.mode} \
      --peak_path="\$WORKDIR/${peak_name}" \
      --model="\$WORKDIR/${model_name}" \
      --output="\$WORKDIR/${sample_name}_xuanjinovo"
    """
}

workflow {
    RUN_XUANJINOVO(
        samples_ch,
        Channel.value(file(params.model_file))
    )
}
