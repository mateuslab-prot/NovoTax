#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 14:54:23 2026

@author: dennis
"""

from ncbi import NCBIProteomeDownloader
from create_db import process_fasta_folder_to_single, build_mmseqs_db

import pandas as pd

df = pd.read_csv('final_reps.tsv', sep='\t')
accessions = list(df['accession'])[:100]

downloader = NCBIProteomeDownloader(api_key='0ae62f0b9fc8beb6201aaa8b2316104d3d09')
downloader.download_proteomes(
    accessions=accessions,
    out_dir='./tmp/',
)

process_fasta_folder_to_single(
    folder='./tmp/',
    output_fasta='test.fasta',
    pattern="*.faa",
    line_width=None,
    parallel=False,
)

build_mmseqs_db('test.fasta', 'test_db')
