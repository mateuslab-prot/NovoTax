"""
Created on Sun Nov 23 23:27:34 2025

@author: densv
"""

import sys
from pathlib import Path
import re
#from .gtdb import GTDB, strip_accession_prefix

GENUS_SCORE_THRESHOLD = 1402

def read_cascadia(file, score_threshold=0.8):
    peptides = dict()
    c = 1
    with open(file) as f:
        header = f.readline()
        for line in f:
            line = line.strip().split('\t')
            prediction = line[3]
            peptide = re.sub(r"\[.*?\]", "", prediction)
            score = float(line[5])
            if score >= score_threshold:
                peptides[str(c)] = peptide
                c += 1
    return peptides

def read_xuanjinovo(file, score_threshold=0.8):
    peptides = dict()
    c = 1
    with open(file) as f:
        header = f.readline().split('\t')
        for line in f:
            spectra, prediction, charge, score = line.split('\t')
            charge, score = int(charge), float(score)
            peptide = re.sub(r"\[.*?\]", "", prediction)
            if score >= score_threshold:
                peptides[str(c)] = peptide
                c += 1
    return peptides

if len(sys.argv) != 5:
    print("Usage: python main.py <sample_name> <input_file> <data_format> <output_file>", file=sys.stderr)
    sys.exit(1)

sample_name = sys.argv[1]
input_file = Path(sys.argv[2])
data_format = sys.argv[3]
output_file = Path(sys.argv[4])

if data_format == 'dia':
    peptides = read_cascadia(input_file)
elif data_format == 'dda':
    peptides = read_xuanjinovo(input_file)

#gtdb = GTDB()

while True:
    
    genus_score = GENUS_SCORE_THRESHOLD + 1
    if genus_score > GENUS_SCORE_THRESHOLD:
        break

with output_file.open('w', encoding='utf-8') as out:
    for peptide, seq in peptides.items():
        out.write(f'>{peptide}\n{seq}\n')
