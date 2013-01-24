#!/usr/bin/python

"""Test script for mysql """

# Inspiration https://github.com/jorgsk/python-bwa-wrapper/blob/master/pipeline.py

import os, time, sys
import glob, re
import MySQLdb
import gc

def main():
	conn = connect()
	cursor = conn.cursor()
 
	fileTypeDict = create_fileTypeDict(cursor)

	# Iterate through projects in the bam_backup folder and adds them into database 
	for project in (glob.glob("/data2/archive/bam_backup/*")):

        	# If it is a directory within bam_bacup, then it is a project.
		if os.path.isdir(project):
 			# Add project name to Analysis Portal
			projectName = os.path.basename(project)
			
			sql = """INSERT INTO 
				study (version, name) 
				VALUES (0, %s)"""
			params = projectName       		
        		
			execute_insert(conn, cursor, sql, params)

			cursor.execute("""SELECT id FROM study WHERE name = %s""", (projectName))
			projectID=cursor.fetchone()[0]					
			
			# Iterate through samples in each project and adds them into database
	        	for sample in glob.glob("%s/*" % project):
			
				# Assume every directory in the project folder is a Sample folder
			        if os.path.isdir(sample):

					# Add sample to Analysis Portal
	                        	sampleName = os.path.basename(sample).replace("Sample_", "");
					# Sample Status ID: 1 - In Progress, 2 - Aligned, 3 - Variants Called		
					sampleStatusID = 2
					createdTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getctime(sample)))

					sql = """INSERT INTO 
						sample (version, assigned_id, created, status_id, study_id) 
						VALUES (0, %s, %s, %s, %s)""" 
					
					params = (sampleName, createdTime, sampleStatusID, projectID)
					#print params
					execute_insert(conn, cursor, sql, params)

		                        cursor.execute("""SELECT id FROM sample WHERE assigned_id = %s""", (sampleName))
		                        sampleID=cursor.fetchone()[0]

					# Find all the files in each folder and add the path to the database. For each file type, find the file type.
					for dirpath, subdirs, files in os.walk(sample):
						for basename in files:
							fullpath = os.path.join(dirpath, basename).replace("/data2/", "http://172.31.104.12/")
							
							fileTypeID = get_fileTypeID(fileTypeDict, dirpath, basename)
							
							if (fileTypeID > 0):
                                      				sql = """INSERT INTO 
                                                		file (version, path, sample_id, type_id) 
                                                		VALUES (0, %s, %s, %s)"""
							
								params = (fullpath, sampleID, fileTypeID)

								execute_insert(conn, cursor, sql, params)

	conn.close()
	cursor.close()
	gc.collect()

def get_fileTypeID(fileTypeDict, dirpath, filename):
	fileTypeID = 0

	if dirpath.endswith("bamqc"):
             	fileTypeID = fileTypeDict.get("QC: Assembly", "0")
        elif dirpath.endswith("fastqc"):
             	fileTypeID = fileTypeDict.get("QC: Sequencing", "0")
        elif dirpath.endswith("coverage"):
             	fileTypeID = fileTypeDict.get("QC: Coverage", "0")
        elif filename.endswith("bam"):
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

def execute_insert(conn, cursor, sql, params):
	try:
    		cursor.execute(sql, params)
                conn.commit()
        except MySQLdb.Error, e:
                # Ignore duplication errors
                if e.args[0] != 1062:
        		print "Error %d: %s" % (e.args[0], e.args[1])
             	conn.rollback()

def select_all():
        cursor.execute("""SELECT name FROM file_type""")

        #Alternatively, can fetch results one at a time using cursor.fetchone
        # Fetched results are stored in arrays
        results = cursor.fetchall()

        for result in results:
                print "%s" % (result[0])

        print "Number of rows returned: %d" % (cursor.rowcount)


def list_samples():
   for project in (glob.glob("/data2/archive/bam_backup/*")):
	if os.path.isdir(project):
   		for sample in glob.glob("%s/*" % project):
			projectName = os.path.basename(project)
			sampleName = os.path.basename(sample)
			print "%s.%s" % (projectName, sampleName)

def connect():
        try:
                conn = MySQLdb.connect(host="localhost", user="pipeline", passwd="2Tilapia", db="analysis")
                return conn
        except MySQLdb.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
                sys.exit(1)

#...

main()
