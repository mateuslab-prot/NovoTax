process RUN_XUANJINOVO {
    label 'gpu'
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

    python -m XuanjiNovo.XuanjiNovo \
      --mode=${params.mode} \
      --peak_path="\$WORKDIR/${peak_name}" \
      --model="\$WORKDIR/${model_name}" \
      --output="\$OUT_DIR"

    cp "\$OUT_DIR/denovo.tsv" "\$WORKDIR/${sample_name}_xuanjinovo.tsv"
    """
}

process RUN_CASCADIA_WITH_MODEL {
    label 'gpu'
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

process RUN_CASCADIA_BUILTIN_MODEL {
    label 'gpu'
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