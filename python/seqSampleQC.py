#!/usr/local/bin/python3
# Scripts for converting .BED files to .interval_list files
# BED files are used by the coverage scripts while .interval_list are used by auto-classification

import os, time, sys
import fileinput
import argparse
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

def main():

	html_doc = "/data2/analysis/120626_SN968_0118_AD149JACXX/Basecall_Stats_D149JACXX/Demultiplex_Stats.htm"

	soup = BeautifulSoup(open(html_doc))

	tables = soup.findAll("table")

	#firstTable = tables[0]
	#for rowHeader in firstTable.findAll('th'):
	#	print (rowHeader.string)

	secondTable  = tables[1]

	avgYield = 0
	avgPctGTQ30 = 0
	avgMeanQScore = 0
	numSamples = 0
	getcontext().prec = 4

	for row in secondTable.findAll('tr'):
		rowContents = row.findAll('td')
		laneNo = rowContents[0].string
		sampleID = rowContents[1].string # Use for sequenced_sample QC
		refSpecies = rowContents[2].string # Use for sequenced_sample QC
		project = rowContents[6].string
		yieldBases = rowContents[7].string.replace(",", "") # Use for sequenced_sample QC
		pctGTQ30 = rowContents[13].string.replace(",", "")
		meanQScore = rowContents[14].string.replace(",", "")

		if (refSpecies != 'unknown'):
			#print (laneNo, sampleID, refSpecies, project, sep=" ")
			#print (yieldBases, pctGTQ30, meanQScore, sep=" ")
			avgPctGTQ30 += float(pctGTQ30) if '.' in pctGTQ30 else int(pctGTQ30)  
			avgMeanQScore += float(meanQScore) if '.' in meanQScore else int(meanQScore)     
			numSamples += 1
		else:
			avgPctGTQ30 /= numSamples
			avgMeanQScore /= numSamples
			
			print ("LaneNo: ", laneNo)
			print ("Avg % GT 30: ", avgPctGTQ30)
			print ("Avg Mean QScore: ", avgMeanQScore)
		
			avgYield = 0
			avgPctGTQ30 = 0
			avgMeanQScore = 0
			numSamples = 0
				
main()
