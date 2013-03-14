#!/usr/local/bin/python3
# Scripts for converting .BED files to .interval_list files
# BED files are used by the coverage scripts while .interval_list are used by auto-classification

import os, time, sys
import fileinput
import argparse

def main():

	parser = argparse.ArgumentParser(description='Script for converting BED files into .interval_lists')
	parser.add_argument('bedFile', help='Path to bedFile')
	args = parser.parse_args()
	infile = open(args.bedFile)
	
	outfileName = os.path.splitext(args.bedFile)[0] + ".interval_list"
	outfile = open(outfileName, 'w')
			
	while 1:
		line = infile.readline()
		if not line:
			break

		line = line.strip()
		lineCol = line.split('\t')
		
		lineCol[0] = lineCol[0].replace("chr", "")
		tempCol = lineCol[3]		
		lineCol[3] = lineCol[5]
		
		lineCol.pop()
		lineCol.pop()
		lineCol.append(tempCol)

		# print (outfileName + ": " + '\t'.join(lineCol))
		
		outfile.write('\t'.join(lineCol) + '\n')
	
	outfile.close()
	infile.close()

main()
