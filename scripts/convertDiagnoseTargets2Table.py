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
parser.add_argument('-d', '--dict', help="Dictionary of Ensembl to Gene Names")
parser.add_argument('-b', '--bed', help='BED file used with DiagnoseTargets')
parser.add_argument('-s', '--samples', help='Samples to consider. Defaults to all samples, comma-separated list')
args = parser.parse_args()

#Set up sample details
samples = args.samples.split(',')
sample_header_list = "\t".join(samples)

sys.stdout.write("Reading DiagnoseTargets file: %s\n" % args.input)
targets_reader = vcf.Reader(open(args.input, 'r'))

regions = defaultdict(lambda: defaultdict(lambda : defaultdict(str)))
sys.stdout.write("Reading BED file: %s\n" % args.bed)
with open(args.bed, 'rU') as csvfile:
    reader = csv.reader(csvfile, dialect='excel-tab')
    for row in reader:
        regions[row[0]][row[1]][row[2]] = row[3]

sys.stdout.write("Reading Dictionary file: %s\n" % args.dict)
gene_dict = dict()
with open(args.dict, 'rU') as csvfile:
    reader = csv.reader(csvfile, dialect='excel-tab')
    for row in reader:
        gene_dict[row[0]] = row[1]

with open(args.output, 'w') as out:
    for record in targets_reader:
        format_fields = record.FORMAT.split(':')
        info_fields = record.INFO.split(';')
        #If no Filter Type definition than all samples passed DiagnoseTargets
        #Filtering criteria, nothing to do
        if format_fields[0] == 'FT':

            #Format sample genotypes in to string
            genotypes = []
            sample_coverage = dict()

            for sample in samples:
                sample_coverage[sample] = record.genotype(sample)['FT']

                 #Retrieve CCDS name info from CCDS BED file and format
                try:
                    region_record = regions[record.CHROM][int(record.POS - 1)][int(record.INFO['END'])]
                except:
                    sys.stderr.write("ERROR: Could not find match in regions dictionary for chrom %s, start %s, end %s\n" %
                                     (record.CHROM, record.POS, record.INFO['END']))
                    region_record = "NA"

