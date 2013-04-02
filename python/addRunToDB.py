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
	parser.add_argument('runFolder', help='Full path to raw run folder (data2/raw/runs/')
	parser.add_argument('runStatus', help='0 if QC required. 2 if RUN failed. 3 if BCL2FASTQ failed')
	args = parser.parse_args()	
	conn = connect()
	cursor = conn.cursor()

	args.runFolder = args.runFolder.rstrip('\/')
	runName = os.path.basename(args.runFolder)

	sql = """SELECT COUNT(id) FROM run WHERE name = '%s'""" % (runName)
	cursor.execute(sql)
	runIDCount = cursor.fetchone()[0]
	runStatus = int(args.runStatus)
	
	if (runIDCount == 0):
		runURL = args.runFolder.replace("/data2/", "http://172.31.104.12/")
		createdTime = "20" + runName[0:2] + "-" + runName[2:4] + "-" + runName[4:6]
		# status_id: 0-QC Required, 1-QC Passed, 2-QC Failed, 3-BCL2FASTQ Failed
		sql = """INSERT INTO run (version, name, status_id, created) VALUES (0, '%s', %d, '%s')""" % (runName, runStatus, createdTime)
		execute_insert(conn, cursor, sql)
	else:
		sql = """UPDATE run SET status_id = %d WHERE name = '%s'""" % (runStatus, runName)
		execute_insert(conn, cursor, sql)

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
