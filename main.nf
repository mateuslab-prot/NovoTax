nextflow.enable.dsl=2

def createDbsPath = params.create_dbs != null
    ? new File(params.create_dbs.toString()).absolutePath
    : null

def gtdbProteinDirPath = params.gtdb_protein_dir != null
    ? new File(params.gtdb_protein_dir.toString()).absolutePath
    : ''

if( params.create_dbs != null ) {
    def createDbsTarget = new File(createDbsPath)

    if( createDbsTarget.exists() && !createDbsTarget.isDirectory() ) {
        error "--create_dbs must point to a directory path, not a file: ${params.create_dbs}"
    }

    if( params.gtdb_protein_dir != null && !file(params.gtdb_protein_dir).exists() ) {
        error "GTDB protein directory not found: ${params.gtdb_protein_dir}"
    }
}
else {
    if( params.samplesheet == null ) {
        error "When running classification, you must provide --samplesheet"
    }

    if( params.model_file != null && !file(params.model_file).exists() ) {
        error "XuanjiNovo model file not found: ${params.model_file}"
    }

    if( params.cascadia_model_file != null && !file(params.cascadia_model_file).exists() ) {
        error "Cascadia model file not found: ${params.cascadia_model_file}"
    }

    if( params.novotax_db_path == null ) {
        error "When running classification, you must provide --novotax_db_path"
    }

    if( !file(params.novotax_db_path).exists() ) {
        error "NovoTax DB directory not found: ${params.novotax_db_path}"
    }

    if( params.novotax_filter_host != null && !file(params.novotax_filter_host).exists() ) {
        error "NovoTax host filter path not found: ${params.novotax_filter_host}"
    }
}

if( params.create_dbs == null ) {
    Channel
        .fromPath(params.samplesheet, checkIfExists: true)
        .splitCsv(header: true, sep: '\t')
        .map { row ->
            def sample_name = row.sample_name?.toString()?.trim()
            def file_path   = row.file_path?.toString()?.trim()
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
}

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

    publishDir { "${params.outdir}" }, mode: 'copy'

    input:
    tuple val(sample_name), path(result_file), val(data_format)
    path novotax_db_dir
    path host_filter_file
    val host_filter_arg

    output:
    tuple val(sample_name), path("novotax_out/${sample_name}")

    script:
    def result_name = result_file.getName()
    def db_dir_name = novotax_db_dir.getName()
    def filterContArg = params.novotax_filter_contaminants ? '--filter_contaminants true' : '--filter_contaminants false'
    def ncbiApiArg = params.novotax_ncbi_api_key ? "--ncbi_api_key \"${params.novotax_ncbi_api_key}\"" : ""

    """
    set -euo pipefail

    WORKDIR="\$(pwd)"
    OUT_ROOT="\$WORKDIR/novotax_out"

    mkdir -p "\$OUT_ROOT"
    rm -rf "\$WORKDIR/mmseqs_dbs"
    ln -s "\$WORKDIR/${db_dir_name}" "\$WORKDIR/mmseqs_dbs"

    python -m NovoTax.cli classify "\$WORKDIR/${result_name}" \\
      -o "\$OUT_ROOT" \\
      ${filterContArg} \\
      ${host_filter_arg} \\
      ${ncbiApiArg} \\
      --genus_score ${params.novotax_genus_score} \\
      --max_iterations ${params.novotax_max_iterations} \\
      --max_strains ${params.novotax_max_strains}
    """
}

process CREATE_NOVOTAX_DBS {
    tag "create_dbs"

    input:
    val db_path
    val gtdb_release
    val gtdb_protein_dir

    script:
    def releaseArg = "--gtdb-release ${gtdb_release}"
    def gtdbArg = gtdb_protein_dir ? "--gtdb-protein-dir \"${gtdb_protein_dir}\"" : ""

    """
    set -euo pipefail

    python -m NovoTax.cli create-dbs "${db_path}" ${releaseArg} ${gtdbArg}
    """
}

workflow {
    if( params.create_dbs != null ) {
        CREATE_NOVOTAX_DBS(
            Channel.value(createDbsPath),
            Channel.value(params.gtdb_release),
            Channel.value(gtdbProteinDirPath)
        )
    }
    else {
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
        novotax_db_ch = Channel.value(file(params.novotax_db_path))

        dummy_host_file = file("${projectDir}/assets/no_host_filter.txt")
        host_filter_file_ch = Channel.value(
            params.novotax_filter_host != null
                ? file(params.novotax_filter_host)
                : dummy_host_file
        )

        host_filter_arg_ch = Channel.value(
            params.novotax_filter_host != null
                ? "--filter_host \"\$(pwd)/${file(params.novotax_filter_host).getName()}\""
                : ""
        )

        RUN_NOVOTAX(
            all_results,
            novotax_db_ch,
            host_filter_file_ch,
            host_filter_arg_ch
        )
    }
}
