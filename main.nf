nextflow.enable.dsl=2


def coalesce(value, fallback) {
    value != null ? value : fallback
}


def absolutePathOrNull(value) {
    value != null ? new File(value.toString()).absolutePath : null
}


def requireExistingFile(pathValue, label) {
    def candidate = file(pathValue)
    if (!candidate.exists() || !candidate.isFile()) {
        error "${label} not found: ${pathValue}"
    }
}


def requireExistingDirectory(pathValue, label, requireNonEmpty = false) {
    def candidate = new File(pathValue.toString())
    if (!candidate.exists()) {
        error "${label} not found: ${pathValue}"
    }
    if (!candidate.isDirectory()) {
        error "${label} is not a directory: ${pathValue}"
    }
    if (requireNonEmpty && ((candidate.listFiles() ?: []) as List).isEmpty()) {
        error "${label} is empty: ${pathValue}"
    }
}


def createDbsPath = absolutePathOrNull(params.create_dbs)
def inputPath = absolutePathOrNull(coalesce(params.input, params.samplesheet))
def outputDirPath = absolutePathOrNull(coalesce(params.output_dir, params.outdir) ?: './results')
def xuanjiModelPath = absolutePathOrNull(coalesce(params.xuanjinovo_model_file, params.model_file))
def cascadiaModelPath = absolutePathOrNull(params.cascadia_model_file)
def gtdbDbDirPath = absolutePathOrNull(coalesce(params.gtdb_db_dir, params.novotax_db_path))
def gtdbProteinRepsPath = absolutePathOrNull(coalesce(params.gtdb_protein_reps, params.gtdb_protein_dir))
def filterHostPath = absolutePathOrNull(coalesce(params.filter_host, params.novotax_filter_host))
def filterContaminants = coalesce(params.filter_contaminants, params.novotax_filter_contaminants)
def ncbiApiKey = coalesce(params.ncbi_api_key, params.novotax_ncbi_api_key)
def genusScore = coalesce(params.genus_score, params.novotax_genus_score) ?: 1275
def maxIterations = coalesce(params.max_iterations, params.novotax_max_iterations) ?: 20
def maxStrains = coalesce(params.max_strains, params.novotax_max_strains) ?: 1000

def runningCreateDbs = createDbsPath != null

new File(outputDirPath).mkdirs()

if (runningCreateDbs) {
    if (gtdbProteinRepsPath == null) {
        error "When running create-dbs, you must provide --gtdb_protein_reps"
    }

    def createDbsTarget = new File(createDbsPath)
    if (createDbsTarget.exists() && !createDbsTarget.isDirectory()) {
        error "--create_dbs must point to a directory path, not a file: ${createDbsPath}"
    }

    requireExistingDirectory(gtdbProteinRepsPath, 'GTDB representative protein directory', true)
} else {
    if (inputPath == null) {
        error "When running the full workflow, you must provide --input"
    }
    requireExistingFile(inputPath, 'Input sample sheet')

    if (xuanjiModelPath != null) {
        requireExistingFile(xuanjiModelPath, 'XuanjiNovo model file')
    }
    if (cascadiaModelPath != null) {
        requireExistingFile(cascadiaModelPath, 'Cascadia model file')
    }

    if (gtdbDbDirPath == null) {
        error "When running classification, you must provide --gtdb_db_dir"
    }
    if (gtdbProteinRepsPath == null) {
        error "When running classification, you must provide --gtdb_protein_reps"
    }

    requireExistingDirectory(gtdbDbDirPath, 'GTDB database directory', true)
    requireExistingDirectory(gtdbProteinRepsPath, 'GTDB representative protein directory', true)

    if (filterHostPath != null) {
        def hostCandidate = file(filterHostPath)
        if (!hostCandidate.exists()) {
            error "Host filter path not found: ${filterHostPath}"
        }
    }
}

if (!runningCreateDbs) {
    Channel
        .fromPath(inputPath, checkIfExists: true)
        .splitCsv(header: true, sep: '\t')
        .map { row ->
            def sampleName = row.sample_name?.toString()?.trim()
            def filePath = row.file_path?.toString()?.trim()
            def dataFormat = row.data_format?.toString()?.trim()?.toLowerCase()

            if (!sampleName || !filePath || !dataFormat) {
                error "Each row in the input TSV must contain sample_name, file_path, and data_format"
            }
            if (!(dataFormat in ['dda', 'dia'])) {
                error "Unsupported data_format '${dataFormat}' for sample '${sampleName}'. Supported values: dda, dia"
            }

            def inputFile = file(filePath)
            if (!inputFile.exists()) {
                error "Input file not found for sample '${sampleName}': ${filePath}"
            }

            tuple(sampleName, inputFile, dataFormat)
        }
        .set { samples_ch }
}

process RUN_XUANJINOVO_WITH_MODEL {
    tag { sample_name }

    input:
    tuple val(sample_name), path(peak_file), val(data_format)
    path model_file

    output:
    tuple val(sample_name), path("${sample_name}/denovo.tsv")

    when:
    data_format == 'dda'

    script:
    def peak_name  = peak_file.getName()
    def model_name = model_file.getName()

    """
    set -euo pipefail
    WORKDIR="\$(pwd)"
    OUT_DIR="\$WORKDIR/${sample_name}_xuanjinovo"

    mkdir -p "${sample_name}"

    export NUMBA_CACHE_DIR="\$WORKDIR/.numba_cache"
    mkdir -p "\$NUMBA_CACHE_DIR"

    python -m XuanjiNovo.XuanjiNovo \
      --mode=${params.mode} \
      --peak_path="\$WORKDIR/${peak_name}" \
      --model="\$WORKDIR/${model_name}" \
      --output="\$OUT_DIR"

    cp "\$OUT_DIR/denovo.tsv" "${sample_name}/denovo.tsv"
    """
}

process RUN_XUANJINOVO_DEFAULT_MODEL {
    tag { sample_name }

    input:
    tuple val(sample_name), path(peak_file), val(data_format)

    output:
    tuple val(sample_name), path("${sample_name}/denovo.tsv")

    when:
    data_format == 'dda'

    script:
    def peak_name = peak_file.getName()

    """
    set -euo pipefail
    WORKDIR="\$(pwd)"
    OUT_DIR="\$WORKDIR/${sample_name}_xuanjinovo"

    mkdir -p "${sample_name}"

    export NUMBA_CACHE_DIR="\$WORKDIR/.numba_cache"
    mkdir -p "\$NUMBA_CACHE_DIR"

    python -m XuanjiNovo.XuanjiNovo \
      --mode=${params.mode} \
      --peak_path="\$WORKDIR/${peak_name}" \
      --model="/opt/models/XuanjiNovo_130M_massnet_massivekb.ckpt" \
      --output="\$OUT_DIR"

    cp "\$OUT_DIR/denovo.tsv" "${sample_name}/denovo.tsv"
    """
}

process RUN_CASCADIA_WITH_MODEL {
    tag { sample_name }

    input:
    tuple val(sample_name), path(input_file), val(data_format)
    path cascadia_model_file

    output:
    tuple val(sample_name), path("${sample_name}/denovo.tsv")

    when:
    data_format == 'dia'

    script:
    """
    set -euo pipefail

    mkdir -p "${sample_name}"

    WORKDIR="\$(pwd)"
    export NUMBA_CACHE_DIR="\$WORKDIR/.numba_cache"
    mkdir -p "\$NUMBA_CACHE_DIR"

    cascadia sequence "${input_file}" "${cascadia_model_file}" -o "${sample_name}/${sample_name}_cascadia"
    cp "${sample_name}/${sample_name}_cascadia.ssl" "${sample_name}/denovo.tsv"
    """
}

process RUN_CASCADIA_DEFAULT_MODEL {
    tag { sample_name }

    input:
    tuple val(sample_name), path(input_file), val(data_format)

    output:
    tuple val(sample_name), path("${sample_name}/denovo.tsv")

    when:
    data_format == 'dia'

    script:
    """
    set -euo pipefail

    mkdir -p "${sample_name}"

    WORKDIR="\$(pwd)"
    export NUMBA_CACHE_DIR="\$WORKDIR/.numba_cache"
    mkdir -p "\$NUMBA_CACHE_DIR"

    cascadia sequence "${input_file}" "/opt/models/cascadia.ckpt" -o "${sample_name}/${sample_name}_cascadia"
    cp "${sample_name}/${sample_name}_cascadia.ssl" "${sample_name}/denovo.tsv"
    """
}

process RUN_NOVOTAX {
    tag { sample_name }

    publishDir { outputDirPath }, mode: 'copy'

    input:
    tuple val(sample_name), path(denovo_file)
    path gtdb_db_dir
    path gtdb_protein_reps
    path host_filter_path
    val use_host_filter

    output:
    tuple val(sample_name), path("${sample_name}")

    script:
    def filterContArg = filterContaminants ? '--filter_contaminants true' : '--filter_contaminants false'
    def filterHostArg = use_host_filter ? "--filter_host \"${host_filter_path}\"" : ''
    def ncbiApiArg = ncbiApiKey ? "--ncbi_api_key \"${ncbiApiKey}\"" : ''

    """
    set -euo pipefail

    python -u -m NovoTax.cli classify "${denovo_file}" \
      --output_dir . \
      --gtdb-db-dir "${gtdb_db_dir}" \
      --gtdb-protein-reps "${gtdb_protein_reps}" \
      ${filterContArg} \
      ${filterHostArg} \
      ${ncbiApiArg} \
      --genus_score ${genusScore} \
      --max_iterations ${maxIterations} \
      --max_strains ${maxStrains}
    """
}

process CREATE_NOVOTAX_DBS {
    tag 'create_dbs'

    publishDir { createDbsPath }, mode: 'copy'

    input:
    val gtdb_release
    path gtdb_protein_reps

    output:
    path('GTDB_r*_filtered_metadata.tsv')
    path('GTDB_r*_extended_genus_reps*')

    script:
    """
    set -euo pipefail

    python -u -m NovoTax.cli create-dbs . \
      --gtdb-protein-reps "${gtdb_protein_reps}" \
      --gtdb-release ${gtdb_release}
    """
}

workflow {
    if (runningCreateDbs) {
        CREATE_NOVOTAX_DBS(
            Channel.value(params.gtdb_release ?: 226),
            Channel.value(file(gtdbProteinRepsPath))
        )
    } else {
        def dda_samples_ch = samples_ch.filter { sample_name, input_file, data_format -> data_format == 'dda' }
        def dia_samples_ch = samples_ch.filter { sample_name, input_file, data_format -> data_format == 'dia' }

        def xuanjinovo_results = xuanjiModelPath != null
            ? RUN_XUANJINOVO_WITH_MODEL(
                dda_samples_ch,
                Channel.value(file(xuanjiModelPath))
            )
            : RUN_XUANJINOVO_DEFAULT_MODEL(dda_samples_ch)

        def cascadia_results = cascadiaModelPath != null
            ? RUN_CASCADIA_WITH_MODEL(
                dia_samples_ch,
                Channel.value(file(cascadiaModelPath))
            )
            : RUN_CASCADIA_DEFAULT_MODEL(dia_samples_ch)

        def all_results = xuanjinovo_results.mix(cascadia_results)
        def gtdb_db_dir_ch = Channel.value(file(gtdbDbDirPath))
        def gtdb_protein_reps_ch = Channel.value(file(gtdbProteinRepsPath))
        def host_filter_file_ch = Channel.value(
            filterHostPath != null
                ? file(filterHostPath)
                : file("${projectDir}/assets/no_host_filter.txt")
        )
        def use_host_filter_ch = Channel.value(filterHostPath != null)

        RUN_NOVOTAX(
            all_results,
            gtdb_db_dir_ch,
            gtdb_protein_reps_ch,
            host_filter_file_ch,
            use_host_filter_ch
        )
    }
}
