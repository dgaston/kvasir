__author__ = 'dan'

import csv
import sys
import argparse

from collections import defaultdict

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', help="Input variants file")
parser.add_argument('-o', '--output', help="Output variants file")
args = parser.parse_args()

gene_counts = defaultdict(int)

with open(args.input, 'rU') as variants:
    reader = csv.DictReader(variants, dialect='excel-tab')
    for row in reader:
        gene_counts[row['gene']] += 1

with open(args.input, 'rU') as variants:
    reader = csv.DictReader(variants, dialect='excel-tab')
    with open(args.output, 'w') as output:
        writer = csv.DictWriter(output, fieldnames=reader.fieldnames, dialect='excel-tab')
        for row in reader:
            if gene_counts[row['gene']] > 1:
                writer.writerow(row)