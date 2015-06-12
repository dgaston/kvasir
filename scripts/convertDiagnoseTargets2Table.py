__author__ = 'dan'

import sys
import argparse
import csv
import vcf
import pybedtools
import tabix
from collections import defaultdict

#Arguments and commenad line parsing
parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', help="Input vcf file")
parser.add_argument('-o', '--output', help="Output text file")
parser.add_argument('-b', '--bed', help='BED file used with DiagnoseTargets')
args = parser.parse_args()

sys.stdout.write("Reading DiagnoseTargets file: %s\n" % args.input)
targets_reader = vcf.Reader(open(args.input, 'r'))

regions = defaultdict(lambda: defaultdict(lambda : defaultdict(str)))
sys.stdout.write("Reading BED file: %s\n" %args.bed)
with open(args.bed, 'rU') as csvfile:
    reader = csv.reader(csvfile, dialect='excel-tab')
    for row in reader:
        regions[row[0]][row[1]][row[2]] = row[3]

with open(args.output, 'w') as out:
    for record in targets_reader:
