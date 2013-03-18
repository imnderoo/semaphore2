#!/usr/local/bin/python3
# Scripts for converting .BED files to .interval_list files
# BED files are used by the coverage scripts while .interval_list are used by auto-classification

import os, time, sys
import fileinput
import argparse
import xml.etree.ElementTree as ET
import argparse
from decimal import *
from bs4 import BeautifulSoup

def main():

	parser = argparse.ArgumentParser(description='Script for converting BED files into .interval_lists')
	parser.add_argument('runID', help='runID')
	args = parser.parse_args()
	
	runID = args.runID
	
	conn = connect()
	cursor = conn.cursor()
	
	# Create QC Metrics Dictionary: Contains 8 dictionary, 1 for each lane. 
	# Each dictionary will contain qc metrics
	qcDict = createQCDict()
	
	for 
	
	"""
		Go into /data2/raw/runs/runID/Data/reports/ to extract cluster density
			- Cluster Density ("NumClusters By Lane.xml") - Need to be 750K to 800K avg
			- Cluster Density ("NumClusters By Lane PF.xml") - Need to be above 80% avg
	"""
		parseClusterDensity(runID, qcDict)
		
	""""
		Go into /data2/raw/runs/runID/Data/reports/ to extract read summary metrics
		
		- number of clusters
		- intensity: 1st cycle
		- intensity: after 20 cycle
	"""	
		parseReadSummary(runID, qcDict)
	
		# To get the flowCellID, split by "_", take the last element [-1] and strip first letter [1:]
		flowCellID = args.runID.split("_")[-1][1:]
	
		demultiFile = "/data2/analysis/" + runID + "/BaseCall_Stats_" + flowCellID + "/Demultiplex_Stats.htm"
		# soup = BeautifulSoup(open(demultiFile))		
	
	"""
		Future TO-DO:
		Other metrics that may be used?
		
		# - A G C T FWHM - Focus Quality ("Intesnity/Charts_<LaneNum>.xml") - Not included atm
		# - A G C T Intensity Quality ("Intensity/Charts_<LaneNum>.xml") - Not included atm

		- Interop Files: Binary files. 
			- Tile, Cycle, Read level metrics

	"""
	
def createQCDict():
	qcDict = {}

	# Create 8 dictionary entries. 1 for each lane. 
	for lane in range(1,9):
		# Each lane will be its own dictionary of values.	
		qcDict[lane]={}

	return qcDict
	
def parseReadSummary(runID, qcDict):

	readSummaryFile = "/data2/raw/runs/" + args.runID + "/Data/reports/Summary/read2.xml"

	tree = ET.parse(readSummaryFile)	
	root = tree.getroot()

	for child in root:
		lane = child.attrib['key']

		qc_Dict[lane]['clusters_raw_mean'] = child.attrib['ClustersRaw']
		qc_Dict[lane]['clusters_raw_sd'] = child.attrib['ClustersRawSD']
		qc_Dict[lane]['clusters_pf_mean'] = child.attrib['ClustersPF']
		qc_Dict[lane]['clusters_pf_sd'] = child.attrib['ClustersPFSD']
		qc_Dict[lane]['pct_clusters_pf_mean'] = child.attrib['PrcPFClusters']
		qc_Dict[lane]['pct_clusters_pf_sd'] = child.attrib['PrcPFClustersSD']
		qc_Dict[lane]['first_cycle_intense_pf_mean'] = child.attrib['FirstCycleIntPF']
		qc_Dict[lane]['first_cycle_intense_pf_sd'] = child.attrib['FirstCycleIntPFSD']
		qc_Dict[lane]['pct_intense20cycle_pf_mean'] = child.attrib['PrcIntensityAfter20CyclesPF']
		qc_Dict[lane]['pct_intense20cycle_pf_sd'] = child.attrib['PrcIntensityAfter20CyclesPFSD']


	# print (laneNo, clustersRaw_Mean, clustersRaw_SD, clustersPF_Mean, clustersPF_SD, sep="  ")
	# print (laneNo, pctClustersPF_Mean, pctClustersPF_SD, firstCycleIntensePF_Mean, firstCycleIntensePF_SD, pctIntense20CyclePF_Mean, pctIntense20CyclePF_SD, sep="  ")
	
		
def parseClusterDensity(runID, qcDict)

	# Parse all cluster dense
	clusterDenseFile = "/data2/raw/runs/" + runID + "/Data/reports/NumClusters By Lane.xml"
	tree = ET.parse(clusterDenseFile)
	root = tree.getroot()
	
	for child in root:
		lane = child.attrib['key'] # May need to convert from String to Int

		qc_Dict[lane]['clusters_dense_min'] = child.attrib['min']
		qc_Dict[lane]['clusters_dense_max'] = child.attrib['max']
		qc_Dict[lane]['clusters_dense_med'] = child.attrib['p50']

	# Parse cluster dense that passed filter (PF)
	clusterDensePFFile = "/data2/raw/runs/" + runID + "/Data/reports/NumClusters By Lane PF.xml"
	tree= ET.parse(clusterDensePFFile)
	root = tree.getroot()

	for child in root:
		lane = child.attrib['key']
		qc_Dict[lane]['clusters_dense_pf_min'] = child.attrib['min']
		qc_Dict[lane]['clusters_dense_pf_max'] = child.attrib['max']
		qc_Dict[lane]['clusters_dense_pf_med'] = child.attrib['p50']			

def execute_insert(conn, cursor, sql):
	try:
		cursor.execute(sql)
		conn.commit()
	except pymysql.Error as e: 
                # Ignore duplication errors
		print ("Error when executing", sql, ":", e, sep=" ")
		conn.rollback()

def connect():
        try:
                conn = pymysql.connect(host="localhost", user="pipeline", passwd="2Tilapia", db="analysis")
                return conn
        except pymysql.Error as e:
                print ("Error connecting to DB", e.args[0], sep=" ")
                sys.exit(1)

main()
