#!/usr/local/bin/python3
# Scripts for converting .BED files to .interval_list files
# BED files are used by the coverage scripts while .interval_list are used by auto-classification

import os, time, sys, gc
import re
import fileinput
import argparse
import xml.etree.ElementTree as ET
import argparse
import pymysql
from decimal import *
from bs4 import BeautifulSoup

def main():

	parser = argparse.ArgumentParser(description='Extract QC metric for each sample found in run')
	parser.add_argument('runFolder', help='runFolder')
	args = parser.parse_args()
	
	runFolder = args.runFolder.rstrip('\/')
	runName = os.path.basename(runFolder)

	conn = connect()
	cursor = conn.cursor()
	
	# Find runID from MYSQL DB
	sql = """SELECT COUNT(id) FROM run WHERE name = '%s'""" % (runName)
	cursor.execute(sql)
	runIDCount = cursor.fetchone()[0]
	
	if(runIDCount == 0):
		print ("The run " + runName + "has not been registered. Please run 'addRunToDB.py'")
	else:
		sql = """ SELECT id FROM run WHERE name = '%s'""" %(runName)
		cursor.execute(sql)
		runID=cursor.fetchone()[0]
	
		yieldDict = createYieldDict()	
			
		for projectFolder in os.listdir(args.runFolder):
			if projectFolder.startswith("Project_"):
				projectName = projectFolder.replace("Project_", "")
				projectPath = os.path.join(args.runFolder, projectFolder)
			
				for sampleFolder in os.listdir(projectPath):
					if sampleFolder.startswith("Sample_"):
						sampleName = sampleFolder.replace("Sample_", "")
				
						sql = """SELECT COUNT(id) FROM sample WHERE assigned_id = '%s'""" % (sampleName)	
						cursor.execute(sql)
						sampleIDCount=cursor.fetchone()[0]	
				
						if(sampleIDCount == 0):
							print ("The sample " + sampleName + " has not been added. Please run 'addSeqSampleToDB.py'")
						else:
							sql = """SELECT id FROM sample WHERE assigned_id = '%s'""" % (sampleName)	
							cursor.execute(sql)
							sampleID = cursor.fetchone()[0]	
			
							sql = """SELECT COUNT(id) FROM sequenced_sample WHERE run_id = %d AND sample_id = %d""" % (runID, sampleID)
							cursor.execute(sql)
							seqSampleIDCount=cursor.fetchone()[0]

							if(seqSampleIDCount == 0):
								print ("The seqSample " + sampleName  + " has not been added. Please run 'addSeqSampleToDB.py'")
							else:
	
								sql = """SELECT id FROM sequenced_sample WHERE run_id = %d AND sample_id = %d""" % (runID, sampleID)
								cursor.execute(sql)
								seqSampleID = cursor.fetchone()[0]

								bamqcPath = os.path.join(projectPath, sampleFolder, "bamqc")
						
								if os.path.isdir(bamqcPath):
									# Each dictionary will contain qc metrics
									qcDict = createQCDict()
	
									qcFilePrefix = bamqcPath + "/" + projectName + "." + sampleName
									# Go into /data2/raw/runs/runID/Data/reports/ to extract cluster density
									parseSamStats(qcFilePrefix, qcDict)
									parsePicardStats(qcFilePrefix, qcDict)
									parsePicardInsert(qcFilePrefix, qcDict)
									parsePicardGCBias(qcFilePrefix, qcDict)
									parseYield(runName, yieldDict)
							
									demultiFile = "/data2/analysis/" + runName + "/Basecall_Stats_" + flowCellID + "/Demultiplex_Stats.htm" 
									samFile = qcFilePrefix + ".samstats.html" 

									if os.path.exists(demultiFile) and os.path.exists(samFile):

										yieldBases = yieldDict[sampleName]
														
										fieldNames = "version,seq_sample_id,yield"
										fieldValues = "0," + str(seqSampleID) + "," + yieldBases

										for metrics in qcDict:
											fieldNames = fieldNames + "," + metrics
											fieldValues = fieldValues + "," + str(qcDict[metrics])

										sql = "INSERT INTO sequenced_sample_qc (" + fieldNames + ") VALUES (" + fieldValues + ")"
										# print ("\t" + sql)
		
										execute_insert(conn, cursor, sql)
									
	conn.close()
	cursor.close()
	gc.collect()				
									
def createQCDict():
	qcDict = {}
	return qcDict

def createYieldDict():
	yieldDict = {}
	return yieldDict

def parseYield(runName, yieldDict):
	flowCellID = runName.split("_")[-1][1:]
	
	demultiFile = "/data2/analysis/" + runName + "/Basecall_Stats_" + flowCellID + "/Demultiplex_Stats.htm"
	soup = BeautifulSoup(open(demultiFile))

	tables = soup.findAll("table")
	secondTable = tables[1]

	for row in secondTable.findAll('tr'):
		rowContents = row.findAll('td')
		sampleID = rowContents[1].string # Use for sequenced_sample QC
		yieldBases = rowContents[7].string.replace(",", "") # Use for sequenced_sample QC

		if not "lane" in sampleID:
			yieldDict[sampleID] = yieldBases

def parseSamStats(qcFilePrefix, qcDict):
	samFile = qcFilePrefix + ".samstats.html"

	if os.path.isfile(samFile):
		buf = readFileToBuffer(samFile)

		for line in buf:
			p = re.compile("ctx\.fillText\(\"MAPQ \>\= 30 \((\d*\.\d)(.*)")
			m = p.match(line)
	
			if m:
				qcDict['pct_gt_mapq30'] = m.group(1)
				break

def parsePicardInsert(qcFilePrefix, qcDict):
	insFile = qcFilePrefix + ".picard.insert.txt"
	if os.path.isfile(insFile):
		buf = readFileToBuffer(insFile)
		
		#line = buf[6] # The category headers
		line = buf[7].rstrip('\r\n') # The values

		metrics = line.split("\t")

		qcDict['insert_size_mean'] = metrics[4]
		qcDict['insert_size_sd'] = metrics[5]

def parsePicardStats(qcFilePrefix, qcDict):
	statsFile = qcFilePrefix + ".picard.alignstat.txt"
	if os.path.isfile(statsFile):
		buf = readFileToBuffer(statsFile)
		
		#line = buf[6] # The category headers
		line = buf[7].rstrip('\r\n') # The values	

		metrics = line.split("\t")

		qcDict['reads_total_pf'] = metrics[1]
		qcDict['pct_reads_aligned_pf'] = 100 * float(metrics[6])
		qcDict['pct_mismatch'] = 100 * float(metrics[12])
		qcDict['pct_indel'] = 100 * float(metrics[14])
		qcDict['read_length_mean'] = metrics[15]
		qcDict['pct_reads_aligned_in_pairs'] = 100 * float(metrics[17])
		qcDict['strand_balance'] = 100 * float(metrics[19])

def parsePicardGCBias(qcFilePrefix,qcDict):
	gcFile = qcFilePrefix + ".picard.gcbias.summary"
	if os.path.isfile(gcFile):
		buf = readFileToBuffer(gcFile)
	
		#line = buf[6] # The category headers
		line = buf[7].rstrip('\r\n') # The values

		metrics = line.split("\t")
	
		qcDict['at_dropout'] = metrics[3]
		qcDict['gc_dropout'] = metrics[4]
		
def readFileToBuffer(fileName):
	fh = open(fileName, 'r')
	buf = fh.readlines()
	fh.close()

	return buf

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
