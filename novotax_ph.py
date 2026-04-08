#!/usr/bin/env python3

import sys
from pathlib import Path

if len(sys.argv) != 4:
    print("Usage: python count_lines.py <sample_name> <input_file> <output_file>", file=sys.stderr)
    sys.exit(1)

sample_name = sys.argv[1]
input_file = Path(sys.argv[2])
output_file = Path(sys.argv[3])

with input_file.open("r", encoding="utf-8", errors="replace") as fh:
    n_lines = sum(1 for _ in fh)

message = f"{sample_name}\t{input_file.name}\t{n_lines}\n"
print(message, end="")

with output_file.open("w", encoding="utf-8") as out:
    out.write(message)
