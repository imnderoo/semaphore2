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
	parser = argparse.ArgumentParser(description='Script for updating paths to output files in analysis DB.')
	parser.add_argument('projectFolder', help='Full path to project folder')
	args = parser.parse_args()	

	conn = connect()
	cursor = conn.cursor()
 
	fileTypeDict = create_fileTypeDict(cursor)

	args.projectFolder = args.projectFolder.rstrip('\/')
	projectName = os.path.basename(args.projectFolder).replace("Project_", "")

	sql = """INSERT INTO study (version, name) VALUES (0, '%s')""" % (projectName)                   
	execute_insert(conn, cursor, sql)

	sql = """SELECT id FROM study WHERE name = '%s'""" % (projectName)
	cursor.execute(sql)
	projectID = cursor.fetchone()[0]
	vcfLoc = ""

	# Iterate through files in project folder - extract  VCF and AnnoVar
	for item in os.listdir(args.projectFolder):
		if item.endswith(".recal.filtered.snps.vcf"):
			vcfLoc = os.path.join(args.projectFolder, item).replace("/data2/", "http://172.31.104.12/")

	print (vcfLoc)

	# Iterate through dirs in project folder
	for item in os.listdir(args.projectFolder):
		#fullpath = os.path.join(dirpath, basename).replace("/data2/", "http://172.31.104.12/")
		fullpath = os.path.join(args.projectFolder, item)
		
		if "Sample_" in fullpath:
			sampleName = os.path.basename(fullpath).replace("Sample_", "")
			sampleStatusID = 2
			createdTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getctime(fullpath)))
			
			sql = """INSERT INTO sample (version, assigned_id, created, status_id, study_id) VALUES (0, '%s', '%s', %d, %d)""" % (sampleName, createdTime, sampleStatusID, projectID)
			execute_insert(conn, cursor, sql)

			sql = """SELECT id FROM sample WHERE assigned_id = '%s'""" % (sampleName)
			cursor.execute(sql)
			sampleID=cursor.fetchone()[0]

			# Update VCF file for this sample
			fileTypeID = get_fileTypeID(fileTypeDict, "", vcfLoc)
			sql = """INSERT INTO file (version, path, sample_id, type_id) VALUES (0, '%s', %s, %s)""" % (vcfLoc, sampleID, fileTypeID)
			execute_insert(conn, cursor, sql)

			# Find all the files in each folder and add the path to the database. For each file type, find the file type and update DB
			for dirpath, subdirs, files in os.walk(fullpath):
				for basename in files:
					fullpath = os.path.join(dirpath, basename).replace("/data2/", "http://172.31.104.12/")
							
					fileTypeID = get_fileTypeID(fileTypeDict, dirpath, basename)
							
					if (fileTypeID > 0):
						sql = """INSERT INTO file (version, path, sample_id, type_id) VALUES (0, '%s', %s, %s)""" % (fullpath, sampleID, fileTypeID)
						execute_insert(conn, cursor, sql)

	conn.close()
	cursor.close()
	gc.collect()

def get_fileTypeID(fileTypeDict, dirpath, filename):
	fileTypeID = 0

	if dirpath.endswith("bamqc"):
		fileTypeID = fileTypeDict.get("QC: Assembly", "0")
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

	return fileTypeID

def create_fileTypeDict(cursor):
	fileTypeDict = {}
	cursor.execute("""SELECT id, name FROM file_type""")
	results = cursor.fetchall()

	for result in results:
		fileTypeDict[result[1]] = result[0]
	
	return fileTypeDict

def execute_insert(conn, cursor, sql):
	try:
		cursor.execute(sql)
		conn.commit()
	except pymysql.Error as e: 
                # Ignore duplication errors
		print ("Error when executing", sql, ":", e, sep=" ")
		conn.rollback()

def select_all():
	cursor.execute("""SELECT name FROM file_type""")

        #Alternatively, can fetch results one at a time using cursor.fetchone
        # Fetched results are stored in arrays
	results = cursor.fetchall()

	for result in results:
		print (result[0])

	print ("Number of rows returned:", cursor.rowcount)


def list_samples():
	for project in (glob.glob("/data2/archive/bam_backup/*")):
		if os.path.isdir(project):
			for sample in glob.glob("%s/*" % project):
				projectName = os.path.basename(project)
				sampleName = os.path.basename(sample)
				print (projectName, sampleName, sep=".")

def connect():
        try:
                conn = pymysql.connect(host="localhost", user="pipeline", passwd="2Tilapia", db="analysis")
                return conn
        except pymysql.Error as e:
                print ("Error connecting to DB", e.args[0], sep=" ")
                sys.exit(1)

main()
