#!/usr/local/bin/python3.3

"""Test script for mysql """

# Inspiration https://github.com/jorgsk/python-bwa-wrapper/blob/master/pipeline.py

import os, time, sys
import glob, re
import gc
import argparse
import pymysql

#main()

def main():
	parser = argparse.ArgumentParser(description='Script for updating runs and mapping samples to runs by fetching SampleSheets.')
	parser.add_argument('rawFolder', help='Full path to raw folder where the run folders are transferred to')
	# /data2/raw/runs - HiSeq folder
	# /data2/raw/runs/roger - HiSeq folder
	# /data2/raw/lars - HiSeq folder
	# /data2/raw/lars/miseq/run_folder
 
	args = parser.parse_args()	
	conn = connect()
	cursor = conn.cursor()
	args.rawFolder = args.rawFolder.rstrip('\/')

	# Iterate through folder of raw runs
	for item in os.listdir(args.rawFolder):
		# Identify run folders
		if re.search('[0-9]{6}_SN[0-9]+_.+', item):
			runFolder = os.path.join(args.rawFolder, item)
			runName = item
			print (runName)

			runURL = runFolder.replace("/data2/", "http://172.31.104.12/")

			sql = """INSERT INTO run (version, name, path) VALUES (0, '%s', '%s')""" % (runName, runURL)
			# sql = """UPDATE run SET path = '%s' WHERE name = '%s'""" % (runURL, runName)
			execute_insert(conn, cursor, sql)

			sql = """SELECT id FROM run WHERE name = '%s'""" % (runName)
			cursor.execute(sql)
			runID=cursor.fetchone()[0]

			# Open SampleSheet
			for sampleSheet in os.listdir(runFolder):
				if sampleSheet.startswith("SampleSheet"):
					sampleSheetPath = os.path.join(runFolder, sampleSheet)
					f = open(sampleSheetPath, 'r')
					f.readline()

					for line in f:
						# FCID,lane,sampleID,sampleRefGenome,Index,Descriptor,Control,Recipe,Operator.Project
						sampleLine = line.split(",")

						# SampleName: assignedID
						sampleName = "".join(sampleLine[2].split()) # "".join(str.split()) removes all spaces, including newline and tabs

						# ProjectName
						projectName = sampleLine[9].replace(" ", "") # Remove spaces
						projectName = projectName.replace("_", "") # Remove underlines
						projectName = projectName.replace(".", "") # Remove random periods
						projectName = "".join(projectName.split()) # Remove newlines and tabs
				
						# Add Project from SampleSheet into 
						sql = """INSERT INTO study (version, name) VALUES (0, '%s')""" % (projectName)
						execute_insert(conn, cursor, sql)
						
						sql = """SELECT id FROM study WHERE name = '%s'""" % (projectName)
						cursor.execute(sql)
						projectID=cursor.fetchone()[0]
	
						sampleStatusID = 1 # In Progress

						createdTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getctime(sampleSheetPath)))

						# sql = """INSERT INTO sample (version, assigned_id, created, status_id, study_id, run_id) VALUES (0, '%s', '%s', %d, %d, %d)""" % (sampleName, createdTime, sampleStatusID, projectID, runID)
						sql = """UPDATE sample SET run_id = %d WHERE assigned_id = '%s'""" % (runID, sampleName)
						execute_insert(conn, cursor, sql)

						sql = """SELECT id FROM sample WHERE assigned_id = '%s'""" % (sampleName)
						cursor.execute(sql)
						sampleID=cursor.fetchone()[0]

					f.close()

				
	'''
				# Find all the files in each folder and add the path to the database. For each file type, find the file type and update DB
				for dirpath, subdirs, files in os.walk(fullpath):

					fileTypeID = 4 # QC: Sequencing
 
					for basename in files:
						fullpath = os.path.join(dirpath, basename).replace("/data2/", "http://172.31.104.12/")
							
						if (fileTypeID > 0):
							sql = """INSERT INTO file (version, path, sample_id, type_id) VALUES (0, '%s', %s, %s)""" % (fullpath, sampleID, fileTypeID)
							execute_insert(conn, cursor, sql)

	'''

	conn.close()
	cursor.close()
	gc.collect()

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
