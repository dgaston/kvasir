#!/usr/bin/env python

# -*- coding: utf-8 -*-
import sys, argparse, vcf, pybedtools, tabix
from collections import defaultdict

if __name__ == "__main__":
    #Arguments and commenad line parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help="Input vcf file")
    parser.add_argument('-v', '--variants', help="VCF file with variants. (bgzipped and tabix indexed)")
    parser.add_argument('-o', '--output', help="Output text file")
    parser.add_argument('-s', '--samples', help='Samples to consider. Defaults to all samples, comma-separated list')
    parser.add_argument('-c', '--ccds', help='CCDS definitions bed file (bgzipped and tabix indexed')
    args = parser.parse_args()
    
    #Set up sample details
    samples = args.samples.split(',')
    sample_header_list = "\t".join(samples)
    
    #Open files and create relevant objects
    sys.stdout.write("Reading file: %s\n" % args.ccds)
    ccds = tabix.open(args.ccds)
    
    sys.stdout.write("Reading file: %s\n" % args.input)
    targets_reader = vcf.Reader(open(args.input, 'r'))
    
    sys.stdout.write("Reading file: %s\n" % args.variants)
    variants_reader = vcf.Reader(open(args.variants, 'r'))
    
    with open(args.output, 'w') as out:
        out.write("%s\t%s\t%s\t%s\t%s\t%s\n" % ("Chrom", "Start", "End", "CCDS", "Flag", sample_header_list))
        for record in targets_reader:
            format_fields = record.FORMAT.split(':')
            
            #If no Filter Type definition than all samples passed DiagnoseTargets
            #Filtering criteria, nothing to do
            if format_fields[0] == 'FT':
                #Identify any variants detected in the region and in which samples
                #sys.stderr.write("Fetching variants: %s:%s-%s\n" % (record.CHROM, int(record.POS), int(record.INFO['END'])))
                variant_records = variants_reader.fetch(record.CHROM, int(record.POS), int(record.INFO['END']))
                
                #Format sample genotypes in to string
                genotypes = []
                
                #Get sample level variant and coverage data
                sample_variants = defaultdict(int)
                sample_coverage = dict()
                sample_flag = dict()
                flags = []
                
                first = 1
                for variant in variant_records:
                    #sys.stderr.write("Checking for variants in samples\n")
                    for sample in samples:
                        #sys.stderr.write("Checking for variants in sample: %s\n" % sample)
                        call = variant.genotype(sample)
                        if call.is_variant:
                            sample_variants[sample] = sample_variants[sample] + 1
                
                for sample in samples:
                    #sys.stderr.write("Sample: %s\n" % sample)
                    #sys.stderr.write("Checking for coverage in sample: %s\n" % sample)
                    sample_flags = []
                    genotypes.append(record.genotype(sample)['FT'])
                    sample_coverage[sample] = record.genotype(sample)['FT']
                    if record.genotype(sample)['FT'] == 'PASS':
                        sample_flags.append("PASS")
                    else:
                        sample_flags.append("COVERAGE")
                    
                    if sample_variants[sample] >= 1:
                        #sys.stderr.write("Appending Variant flag\n")
                        sample_flags.append("VARIANT")
                    
                    flags.append(",".join(sample_flags))
                
                #Format sample genotypes in to string
                genotypes_string = "\t".join(genotypes)
                flag = ";".join(flags)
                
                #Retrieve CCDS name info from CCDS BED file and format
                try:
                    ccds_records = ccds.query(record.CHROM, int(record.POS), int(record.INFO['END']))
                except:
                    ccds_records = []
                
                if ccds_records:
                    ccds_ids = []
                    for line in ccds_records:
                        ccds_ids.append(line[3])
                    ccds_string = ";".join(ccds_ids)
                else:
                    #sys.stderr.write("CCDS Query Failed\n")
                    ccds_string = "NA"
                
                out.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (record.CHROM, record.POS, record.INFO['END'], ccds_string, flag, genotypes_string) )

sys.stdout.write("Finished!\n")