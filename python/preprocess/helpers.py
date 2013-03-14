#!/usr/bin/python

"""Helper modules for pipelines"""

# Inspiration https://github.com/jorgsk/python-bwa-wrapper/blob/master/pipeline.py

import os, time, sys
import glob, re

def log(value):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
	print >> sys.stderr, "[{0}] {1}: {2}".format(timestamp, os.getpid(), value)

def process_sample_directory(path, read_group, reference, project):
	print "# This Makefile is automatically generated"
	files = glob.glob("%s/*.fastq.gz" % path)
        sample_name = get_sample_name(path)
        if read_group == None:
		read_group = generate_read_group(sample_name)

	print "all: {0}.{1}.recal.filtered.snps.vcf {0}.{1}.clean.dedup.recal.bamqc.out {0}.{1}.snps.R.pdf".format(project, sample_name)

	print_clean()
		
	bams = print_bwa(files, read_group, sample_name)
	print_merge_bams(bams, sample_name)
	print_sort_bam(sample_name)
	print_gatk_process(sample_name, project)
	print_gatk_genotyper(sample_name, project)
	print_gatk_recalibrate(sample_name, project)
	print_bam_qc(sample_name, project)
	print_r_recalibrate(sample_name, project)

def get_sample_name(sample_path):
	return re.match('.*/Sample_([^\/]+)/$', sample_path).groups(1)[0]

def generate_read_group(sample_name):
	return "@RG\tID:%s\tPL:illumina\tPU:barcode\tLB:%s-1\tSM:%s" % (sample_name,sample_name,sample_name)
	exit(0)	

def id_from_path(path):
        # Get the filename
	return os.path.basename(path)

def print_bwa(files, read_group, sample_name):
	pairs = group_files(files)
	for pair in pairs:
                print_bwa_sge_command(pair, read_group, sample_name)
	return map(lambda x: x[0], pairs)

# Group files by R1 and R2
def group_files(files):
        groups = dict()
        # SM1445_CCGTCC_L004_R2_009.fastq.g
        for f in map(lambda x: x, files):
        	res = re.match('.*/([\w\d-]+)_[ACGT-]+_L\d\d\d_R(\d)_(\d\d\d).fastq.gz', f)
		#print res.groups(1)
		key = "{0}_{1}".format(res.groups(1)[0], res.groups(1)[2])	
 		if not key in groups:
			groups[key] = []
		groups[key].append(f)
	return groups.values()
	
def print_bwa_sge_command(pair, read_group, sample_name):
	base_r1 = id_from_path(pair[0])
	base_r2 = id_from_path(pair[1])
	r1_id = base_r1.replace(".fast.gz", "")
	print "\n{0}.bam: {0} {1}".format(base_r1, base_r2)
	print "\tqsub -hard -l slots_limit=3 -l mem_limit=5G -cwd -N bwa.{3} $(NGS_PIPE)/helpers/preprocess/bwa.sge {1} {2} {0}".format(sample_name, base_r1, base_r2, r1_id)
	
def print_merge_bams(files, sample_name):
        files = map(lambda x: id_from_path(x) + ".bam", files)
        print "\n%s.bam: %s" % (sample_name, " ".join(files))
	print "\tqsub -hard -l mem_limit=128M -cwd -N sam.merge.{0} -sync y -hold_jid bwa.{0}* $(NGS_PIPE)/helpers/preprocess/sam.merge.sge {0}.bam {1}".format(sample_name, " ".join(files))

def print_sort_bam(sample_name):
        print "\n{0}.sorted.bam: {0}.bam".format(sample_name)
	print "\tsamtools sort {0}.bam {0}.sorted".format(sample_name)

def print_gatk_process(sample_name, project):
        print "\n{0}.{1}.clean.dedup.recal.bam: {1}.sorted.bam".format(project, sample_name)
	print "\tqsub -hard -l mem_limit=6G -cwd -N gatk.process.{1} -sync y $(NGS_PIPE)/helpers/preprocess/gatk.process.sge {0} {1}".format(project, sample_name)

def print_gatk_genotyper(sample_name, project):
	print "\n{0}.{1}.raw.snps.vcf: {0}.{1}.clean.dedup.recal.bam".format(project, sample_name)
	print "\tqsub -hard -l slots_limit=8 -l mem_limit=14G -cwd -N gatk.genotyper.{0} -sync y $(NGS_PIPE)/helpers/preprocess/gatk.genotyper.sge $? $@".format(sample_name)

def print_gatk_recalibrate(sample_name, project):
	print "\n{0}.{1}.recal.filtered.snps.vcf: {0}.{1}.raw.snps.vcf".format(project, sample_name)
	print "\tqsub -hard -l mem_limit=8G -cwd -N gatk.recal.{1} -sync y $(NGS_PIPE)/helpers/preprocess/gatk.recal.sge $? {0} {1}".format(project, sample_name)

def print_r_recalibrate(sample_name, project):
	print "\n {0}.{1}.snps.R.pdf {0}.{1}.snps.tranches.pdf: {0}.{1}.snps.R {0}.{1}.snps.tranches".format(project, sample_name)
	print "\tR CMD BATCH --no-restore --no-save {0}.{1}.snps.R /dev/null".format(project, sample_name)

def print_bam_qc(sample_name, project):
	print "\n{0}.{1}.clean.dedup.recal.bamqc.out: {0}.{1}.clean.dedup.recal.bam".format(project, sample_name)
	print "\trun_bamqc $? > $@"

def print_clean():
	print "\nclean:"
	print "\trm -rf *.sai *.bam *.out *.bai *.jobreport *.intervals "
