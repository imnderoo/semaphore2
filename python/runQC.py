#!/usr/local/bin/python3
# Scripts for converting .BED files to .interval_list files
# BED files are used by the coverage scripts while .interval_list are used by auto-classification

import os, time, sys
import fileinput
import argparse
import xml.etree.ElementTree as ET
from decimal import *
from bs4 import BeautifulSoup

def main():

	parser = argparse.ArgumentParser(description='Script for converting BED files into .interval_lists')
	parser.add_argument('runID', help='runID')
	args = parser.parse_args()

	"""Go into /data2/raw/runs/runID/Data/reports/ to extract average:
		- Cluster Density ("NumClusters By Lane.xml") - Need to be 750K to 800K avg
		- Cluster Density ("NumClusters By Lane PF.xml") - Need to be above 80% avg
		- ClustersRaw, ClustersRawSD, ClustersPF, ClustersPFSD, PrcPFClusters, PrcPFClustersDF,
		- FirstCycleIntPF, FirstCycleIntPFSD, PrcIntensityAfter20CyclesPF, PrcIntensityAfter20CyclsPFSD
			- All found in (Summary/read2.xml)

		# - A G C T FWHM - Focus Quality ("Intesnity/Charts_<LaneNum>.xml") - Not included atm
		# - A G C T Intensity Quality ("Intensity/Charts_<LaneNum>.xml") - Not included atm

		- Interop Files: Binary files. 
			- Tile, Cycle, Read level metrics

	"""

	clusterDenseFile = "/data2/raw/runs/" + args.runID + "/Data/reports/NumClusters By Lane.xml"
	tree = ET.parse(clusterDenseFile)
	root = tree.getroot()
	
	for child in root:
		laneNo = child.attrib['key']
		clustersDenseMin = child.attrib['min']
		clustersDenseMax = child.attrib['max']
		clustersDenseMed = child.attrib['p50']

	# print(laneNo, clustersDenseMin, clustersDenseMax, clustersDenseMed, sep=" ")

	clusterDensePFFile = "/data2/raw/runs/" + args.runID + "/Data/reports/NumClusters By Lane PF.xml"
	tree= ET.parse(clusterDensePFFile)
	root = tree.getroot()

	for child in root:
		laneNo = child.attrib['key']
		clustersDensePFMin = child.attrib['min']
		clustersDensePFMax = child.attrib['max']
		clustersDensePFMed = child.attrib['p50']		

	# print(laneNo, clustersDensePFMin, clustersDensePFMax, clustersDensePFMed, sep=" ")

	readSummaryFile = "/data2/raw/runs/" + args.runID + "/Data/reports/Summary/read2.xml"

	tree = ET.parse(readSummaryFile)	
	root = tree.getroot()

	for child in root:
		laneNo = child.attrib['key']
		clustersRaw_Mean = child.attrib['ClustersRaw']
		clustersRaw_SD = child.attrib['ClustersRawSD']
		clustersPF_Mean = child.attrib['ClustersPF']
		clustersPF_SD = child.attrib['ClustersPFSD']
		pctClustersPF_Mean = child.attrib['PrcPFClusters']
		pctClustersPF_SD = child.attrib['PrcPFClustersSD']
		firstCycleIntensePF_Mean = child.attrib['FirstCycleIntPF']
		firstCycleIntensePF_SD = child.attrib['FirstCycleIntPFSD']
		pctIntense20CyclePF_Mean = child.attrib['PrcIntensityAfter20CyclesPF']
		pctIntense20CyclePF_SD = child.attrib['PrcIntensityAfter20CyclesPFSD']


	# print (laneNo, clustersRaw_Mean, clustersRaw_SD, clustersPF_Mean, clustersPF_SD, sep="  ")
	# print (laneNo, pctClustersPF_Mean, pctClustersPF_SD, firstCycleIntensePF_Mean, firstCycleIntensePF_SD, pctIntense20CyclePF_Mean, pctIntense20CyclePF_SD, sep="  ")

	# To get the flowCellID, split by "_", take the last element [-1] and strip first letter [1:]
	flowCellID = args.runID.split("_")[-1][1:]
	
	demultiFile = "/data2/analysis/" + args.runID + "/BaseCall_Stats_" + flowCellID + "/Demultiplex_Stats.htm"
	soup = BeautifulSoup(open(demultiFile))		
	
	
	"""
	outfile = open(outfileName, 'w')
			
		outfile.write('\t'.join(lineCol) + '\n')
	
	outfile.close()
	"""
main()
