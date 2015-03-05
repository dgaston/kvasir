#!/usr/bin/env python

# -*- coding: utf-8 -*-
import sys
import subprocess as sub


from config import parseProjectConfig
from multiprocessing import Pool

def runAndLogCommand(command, logfile):
	'''Run a command and log StdErr to file'''
	
	with open(logfile,"wb") as err:
		sys.stdout.write("Executing %s and writing to logfile %s\n" % (command, logfile))
		p = sub.Popen(command, stdout=sub.PIPE, stderr=err, shell=True)
		output = p.communicate()
		code = p.returncode
		if code:
			sys.stdout.write("An error occured. Please check %s for details\n" % logfile)
			err.write("An error occured. Please check %s for details\n" % logfile)
		
		return code

def runMulti(instruction):
	'''Run Mark Duplicates'''
	
	code = runAndLogCommand(instruction[0], instruction[1])
	return code

def checkReturnCodes(codes):
	for code in codes:
		checkReturnCode(code)

def checkReturnCode(code):
	if code:
		sys.stdout.write("One or more processes did not complete successfully. Exiting\n")
		sys.exit()