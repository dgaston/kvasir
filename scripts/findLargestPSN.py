#!/usr/bin/env python

import vcf, sys

vcf_reader = vcf.Reader(open(sys.argv[1], 'r'))
largest = 0
for record in vcf_reader:
    if int(record.INFO['PSN'][0]) > largest:
        largest = int(record.INFO['PSN'][0])
        sys.stdout.write("New largest PSN value is %s\n" % largest)

sys.stdout.write("Largest PSN value was: %s\n" % largest)