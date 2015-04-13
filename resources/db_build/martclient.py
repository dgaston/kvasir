#!/usr/bin/env python

import sys
from bioservices import *

s = BioMart()
ret = s.registry()

with open (sys.argv[1], "r") as myfile:
    data=myfile.read()

res = s.query(data)

print res