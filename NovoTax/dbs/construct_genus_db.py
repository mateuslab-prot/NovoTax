from .ncbi import NCBIProteomeDownloader

species_accessions = ['GB_GCA_002796305.1', 'GB_GCA_016201735.1']

downloader = NCBIProteomeDownloader(api_key='0ae62f0b9fc8beb6201aaa8b2316104d3d09')
downloader.download_proteomes(
    accessions=species_accessions,
    out_dir='./tmp/',
)
