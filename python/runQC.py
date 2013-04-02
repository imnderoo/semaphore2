#!/usr/local/bin/python3
# Scripts for converting .BED files to .interval_list files
# BED files are used by the coverage scripts while .interval_list are used by auto-classification

import os, time, sys, gc
import fileinput
import argparse
import xml.etree.ElementTree as ET
import argparse
import pymysql
from decimal import *
from bs4 import BeautifulSoup

def main():

	parser = argparse.ArgumentParser(description='Extract QC Metrics for the entered run')
	parser.add_argument('runID', help='runID')
	args = parser.parse_args()
	
	conn = connect()
	cursor = conn.cursor()
	
	# Find runID from MYSQL DB
	runID = args.runID.rstrip('\/')
	runID = os.path.basename(runID)
	
	sql = """SELECT COUNT(id) FROM run WHERE name = '%s' """ % (runID)
	cursor.execute(sql)
	runCount = cursor.fetchone()[0]

	if(runCount == 0):
		print ("Run not found in DB. Please run updateRun.sh and updateSeqSample.sh before running QC scripts")
		sys.exit(1)

	sql = """SELECT id FROM run WHERE name = '%s'""" % (runID)
	cursor.execute(sql)
	runID_mysql = cursor.fetchone()[0]
	
	sql = """SELECT COUNT(id) FROM run_qc WHERE run_id = %s""" % (runID_mysql)
	cursor.execute(sql)
	runIDCount = cursor.fetchone()[0]

	if(runIDCount == 0):

		# Create QC Metrics Dictionary: Contains 8 dictionary, 1 for each lane. 
		# Each dictionary will contain qc metrics
		qcDict = createQCDict()
	
		# Go into /data2/raw/runs/runID/Data/reports/ to extract cluster density
		parseClusterDensity(runID, qcDict)
		
		#Go into /data2/raw/runs/runID/Data/reports/ to extract read summary metrics
		parseReadSummary(runID, qcDict)

		# Go into /data2/analysis/runID/Basecall_Stats_flowcellID/Demultiplex_Stats.htm
		parseDemultiplex(runID, qcDict)

		fieldNames = "version"
		fieldValues = "0"

		for laneKey in qcDict:

			fieldNames = fieldNames + ",run_id,lane"
			fieldValues = fieldValues + "," + str(runID_mysql) + "," + str(laneKey)
			# print ("Lane " + str(laneKey))			
			
			for metrics in qcDict[laneKey]:
				fieldNames = fieldNames + "," + metrics
				fieldValues = fieldValues + "," + str(qcDict[laneKey][metrics])
		
				# print ("\t " + metrics + ": " + str(qcDict[laneKey][metrics]))

			sql = "INSERT INTO run_qc (" + fieldNames + ") VALUES (" + fieldValues + ")"			
			execute_insert(conn, cursor, sql)

			# print ("\t" + sql)		
			
			fieldNames = "version"
			fieldValues = "0"

			conn.close()
			cursor.close()
			gc.collect()
		"""
		Other metrics that may be used in the future?
		
		- A G C T FWHM - Focus Quality ("Intesnity/Charts_<LaneNum>.xml")
		- A G C T Intensity Quality ("Intensity/Charts_<LaneNum>.xml")
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

	readSummaryFile = "/data2/raw/runs/" + runID + "/Data/reports/Summary/read1.xml"

	tree = ET.parse(readSummaryFile)	
	root = tree.getroot()

	for child in root:
		lane = int(child.attrib['key'])

		qcDict[lane]['clusters_raw_mean'] = child.attrib['ClustersRaw']
		qcDict[lane]['clusters_raw_sd'] = child.attrib['ClustersRawSD']
		qcDict[lane]['clusters_pf_mean'] = child.attrib['ClustersPF']
		qcDict[lane]['clusters_pf_sd'] = child.attrib['ClustersPFSD']
		qcDict[lane]['pct_clusters_pf_mean'] = child.attrib['PrcPFClusters']
		qcDict[lane]['pct_clusters_pf_sd'] = child.attrib['PrcPFClustersSD']
		qcDict[lane]['first_cycle_intense_pf_mean'] = child.attrib['FirstCycleIntPF']
		qcDict[lane]['first_cycle_intense_pf_sd'] = child.attrib['FirstCycleIntPFSD']
		qcDict[lane]['pct_intense20cycle_pf_mean'] = child.attrib['PrcIntensityAfter20CyclesPF']
		qcDict[lane]['pct_intense20cycle_pf_sd'] = child.attrib['PrcIntensityAfter20CyclesPFSD']


def parseClusterDensity(runID, qcDict):

	# Parse all cluster dense
	clusterDenseFile = "/data2/raw/runs/" + runID + "/Data/reports/NumClusters By Lane.xml"
	tree = ET.parse(clusterDenseFile)
	root = tree.getroot()
	
	for child in root:
		lane = int(child.attrib['key']) # May need to convert from String to Int

		qcDict[lane]['clusters_dense_min'] = child.attrib['min']
		qcDict[lane]['clusters_dense_max'] = child.attrib['max']
		qcDict[lane]['clusters_dense_med'] = child.attrib['p50']

	# Parse cluster dense that passed filter (PF)
	clusterDensePFFile = "/data2/raw/runs/" + runID + "/Data/reports/NumClusters By Lane PF.xml"
	tree= ET.parse(clusterDensePFFile)
	root = tree.getroot()

	for child in root:
		lane = int(child.attrib['key'])
		qcDict[lane]['clusters_dense_pf_min'] = child.attrib['min']
		qcDict[lane]['clusters_dense_pf_max'] = child.attrib['max']
		qcDict[lane]['clusters_dense_pf_med'] = child.attrib['p50']			

def parseDemultiplex(runID, qcDict):
	# To get the flowCellID, split by "_", take the last element [-1] and strip first letter [1:]
	runID = runID.replace("/", "")
	flowCellID = runID.split("_")[-1][1:]

	demultiFile = "/data2/analysis/" + runID + "/Basecall_Stats_" + flowCellID + "/Demultiplex_Stats.htm"
	soup = BeautifulSoup(open(demultiFile))		

	tables = soup.findAll("table")

	secondTable  = tables[1]

	avgPctGTQ30 = 0
	avgMeanQScore = 0
	numSamples = 0

	for row in secondTable.findAll('tr'):
		rowContents = row.findAll('td')
		lane = int(rowContents[0].string)
		sampleID = rowContents[1].string # Use for sequenced_sample QC
		refSpecies = rowContents[2].string # Use for sequenced_sample QC
		project = rowContents[6].string # Not used
		yieldBases = int(rowContents[7].string.replace(",", "")) # Use for sequenced_sample QC

		pctGTQ30 = '0'
		meanQScore = '0'

		if (yieldBases > 0):
			pctGTQ30 = rowContents[13].string.replace(",", "") # Not used
			meanQScore = rowContents[14].string.replace(",", "") # Not used

		if (refSpecies != 'unknown'):
			avgPctGTQ30 += float(pctGTQ30) if '.' in pctGTQ30 else int(pctGTQ30)  
			avgMeanQScore += float(meanQScore) if '.' in meanQScore else int(meanQScore)     
			numSamples += 1
		else:
			avgPctGTQ30 /= numSamples
			avgMeanQScore /= numSamples
			
			qcDict[lane]['pct_gtq30'] = avgPctGTQ30
			qcDict[lane]['qscore_mean'] = avgMeanQScore

			avgPctGTQ30 = 0
			avgMeanQScore = 0
			numSamples = 0


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
