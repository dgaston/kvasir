#!/usr/bin/env python

import HTSeq
import sys, itertools, csv, os

def interleave_fastq(fastq1, fastq2, interleaved):
    '''Interleave paired fastq files'''
    
    outfile = open(interleaved, "w")
    for read1, read2 in itertools.izip(HTSeq.FastqReader(fastq1), HTSeq.FastqReader(fastq2)):
        temp1 = read1.name.split()
        temp2 = read2.name.split()
        read1.name = "%s/1 %s" % (temp1[0], temp1[1])
        read2.name = "%s/2 %s" % (temp2[0], temp2[1])
        
        read1.write_to_fastq_file(outfile)
        read2.write_to_fastq_file(outfile)
    outfile.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f1", "--fastq1", help="Pair1 FastQ")
    parser.add_argument("-f2", "--fastq2", help="Pair2 FastQ")
    parser.add_argument("-i", "--interleaved", help="Name of interleaved fastq file", default="interleaved.fastq")
    parser.add_argument("-e", "--executable", help="MITObim executable", default="MITObim.pl")
    parser.add_argument("-m", "--manifest", help="Manifest containing species in the pools and their reference sequence file")
    args = parser.parse_args()
    
    if(args.fastq1 and args.fastq2):
        sys.stdout.write("Found paired fastq files. Interleaving\n")
        sys.stdout.write("Pair1: %s, Pair2: %s, Output: %s\n" % (args.pair1, args.pair2, args.interleaved))
        
        interleave_fastq(args.fastq1, args.fastq2, args.interleaved)
    
    with open(args.manifest, 'rU') as manifest:
        reader = csv.reader(manifest, delimiter='\t')
        for row in reader:
            sys.stdout.write("Setting up directory %s for species: %s with bait sequence file %s\n" % (row[3], row[0], row[1]))
            os.system("mkdir %s" % row[3])
            os.system("cp %s %s" % (args.interleaved, row[3]))
            os.system("cp %s %s" % (row[1], row[3]))
            os.chdir(row[3])
            sys.stdout.write("Executing: %s -sample testpool -ref bait -readpool %s --quick %s -end 200 --clean &> log" % (args.executable, args.interleaved, row[1]))
            os.system("%s -sample testpool -ref bait -readpool %s --quick %s -end 200 --clean &> log" % (args.executable, args.interleaved, row[1]))

if __name__ == '__main__':
  main()