#!/usr/local/bin/python3
"""Test script for mysql """

# Inspiration https://github.com/jorgsk/python-bwa-wrapper/blob/master/pipeline.py

import os, time, sys
import glob, re
import gc
import argparse
import pymysql

def main():
	parser = argparse.ArgumentParser(description='Script for updating runs and mapping samples to runs by fetching SampleSheets.')
	parser.add_argument('runFolder', help='Full path to analysis run folder (data2/analysis/')
	args = parser.parse_args()	
	conn = connect()
	cursor = conn.cursor()

	fileTypeDict = create_fileTypeDict(cursor)

	args.runFolder = args.runFolder.rstrip('\/')
	runName = os.path.basename(args.runFolder)
	
	runID = getRunIDByName(conn, cursor, runName)

	if runID >= 0:
		# Open SampleSheet
		for projectFolder in os.listdir(args.runFolder):
			if projectFolder.startswith("Project_"):
				projectPath = os.path.join(args.runFolder, projectFolder)
				projectName = projectFolder.replace("Project_", "") 
				projectID = getProjectIDByName(conn, cursor, projectName)
	
				if projectID >= 0:

					for sampleFolder in os.listdir(projectPath):
						if "Sample" in sampleFolder:
							print(sampleFolder)
							sampleName = sampleFolder.replace("Sample_", "")				
							sampleID = getSampleIDByName(conn, cursor, sampleName, projectID)

							if sampleID >= 0:

								sql = """SELECT COUNT(id) FROM sequenced_sample WHERE run_id = %d AND sample_id = %d""" % (runID, sampleID)
								cursor.execute(sql)
								seqSampleIDCount=cursor.fetchone()[0]

								if (seqSampleIDCount == 0):
									sampleStatusID = 0 # No Analysis Ordered
									sql = """INSERT INTO sequenced_sample (version, run_id, sample_id, status_id) VALUES (0, %d, %d, %d)""" % (runID, sampleID, sampleStatusID)
									execute_insert(conn, cursor, sql)				
	
								sql = """SELECT id FROM sequenced_sample WHERE run_id = %d AND sample_id = %d""" % (runID, sampleID)
								cursor.execute(sql)
								seqSampleID = cursor.fetchone()[0]
					
								sampleRelPath = os.path.join(projectPath, sampleFolder)
								samplePath = os.path.abspath(sampleRelPath)
					
								for dirpath, subdirs, files in os.walk(samplePath):
									for basename in files:
										filePath = os.path.join(dirpath, basename).replace("/data2/", "http://172.31.104.12/")
							
										sql = """SELECT COUNT(id) FROM file WHERE seq_sample_id = %d AND path = '%s'""" % (seqSampleID, filePath)		
										cursor.execute(sql)
										fileIDCount = cursor.fetchone()[0]

										fileTypeID = get_fileTypeID(fileTypeDict, dirpath, basename)
							
										if (fileTypeID >= 0 and fileIDCount == 0):
											sql = """INSERT INTO file (version, path, seq_sample_id, type_id) VALUES (0, '%s', %d, %d)""" % (filePath, seqSampleID, fileTypeID)
											execute_insert(conn, cursor, sql)
							
										sql = """SELECT status_id FROM sequenced_sample WHERE id = %d""" % (seqSampleID)
										cursor.execute(sql)
										seqStatus = cursor.fetchone()[0]

										if (fileTypeID == 1 and seqStatus < 2):
											sql = """UPDATE sequenced_sample SET status_id = 2 WHERE id = %d""" % (seqSampleID)
											execute_insert(conn, cursor, sql)
										elif (fileTypeID == 2 and seqStatus < 3):
											sql = """UPDATE sequenced_sample SET status_id = 3 WHERE id = %d""" % (seqSampleID)
											execute_insert(conn, cursor, sql)
					
	conn.close()
	cursor.close()
	gc.collect()

def getRunIDByName(conn, cursor, runName):
	sql = """SELECT COUNT(id) FROM run WHERE name = '%s'""" % (runName)
	cursor.execute(sql)
	runIDCount=cursor.fetchone()[0]

	runID=-1

	if(runIDCount == 0):
		print ("The run" + runName + "has not been registered. Please run 'addRun2DB.py'")
	else:
		sql = """SELECT id FROM run WHERE name = '%s'""" % (runName)
		cursor.execute(sql)

		try:
			runID=cursor.fetchone()[0]	
		except Exception as e:
			print ("Error while updating run " + runName)
			print (e)
			print (" ")

	return runID

def getProjectIDByName(conn, cursor, projectName):
	sql = """SELECT COUNT(id) FROM study WHERE name = '%s'""" % (projectName)
	cursor.execute(sql)
	projectIDCount=cursor.fetchone()[0]

	if (projectIDCount == 0):
		# Add Project from SampleSheet into 
		sql = """INSERT INTO study (version, name) VALUES (0, '%s')""" % (projectName)
		execute_insert(conn, cursor, sql)
						
	sql = """SELECT id FROM study WHERE name = '%s'""" % (projectName)
	cursor.execute(sql)

	projectID=-1

	try:
		projectID=cursor.fetchone()[0]
	except Exception as e:
		print ("Error while updating project " + projectName)
		print (e)
		print (" ")

	return projectID

def getSampleIDByName(conn, cursor, sampleName, projectID):
	sql = """SELECT COUNT(id) FROM sample WHERE assigned_id = '%s'""" % (sampleName)
	
	cursor.execute(sql)
	sampleIDCount=cursor.fetchone()[0]

	if (sampleIDCount == 0):
		sql = """INSERT INTO sample (version, assigned_id, study_id) VALUES (0, '%s', %d)""" % (sampleName, projectID)
		execute_insert(conn, cursor, sql)

	sql = """SELECT id FROM sample WHERE assigned_id = '%s'""" % (sampleName)	
	cursor.execute(sql)
	
	sampleID=-1				

	try:
		sampleID=cursor.fetchone()[0]
	except Exception as e:
		print ("Error while updating sample " + sampleName)
		print (e)
		print (" ")
	
	return sampleID

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
                
def get_fileTypeID(fileTypeDict, dirpath, filename):
	fileTypeID = -1

	if dirpath.endswith("bamqc") and filename.endswith(".png"):
		fileTypeID = fileTypeDict.get("QC: Alignment", "0")
	elif dirpath.endswith("fastqc"):
		fileTypeID = fileTypeDict.get("QC: Sequencing", "0")
	elif filename.endswith(".plot.pdf"):
		fileTypeID = fileTypeDict.get("QC: Coverage", "0")
	elif filename.endswith("coverage.summary"):
		fileTypeID = fileTypeDict.get("QC: Coverage", "0")
	elif filename.endswith(".clean.dedup.recal.bam"):
		fileTypeID = fileTypeDict.get("BAM", "0")
	elif filename.endswith(".recal.filtered.snps.vcf"):
		fileTypeID = fileTypeDict.get("VCF", "0")
	elif filename.endswith(".fastq.gz"):
		fileTypeID = fileTypeDict.get("FASTQ", "0")

	return fileTypeID

def create_fileTypeDict(cursor):
	fileTypeDict = {}
	cursor.execute("""SELECT id, name FROM file_type""")
	results = cursor.fetchall()

	for result in results:
		fileTypeDict[result[1]] = result[0]
	
	return fileTypeDict

main()
