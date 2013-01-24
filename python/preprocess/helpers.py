#!/usr/bin/python

"""Helper modules for pipelines"""

# Inspiration https://github.com/jorgsk/python-bwa-wrapper/blob/master/pipeline.py

import os, time, sys
import glob, re

def log(value):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
	print >> sys.stderr, "[{0}] {1}: {2}".format(timestamp, os.getpid(), value)

#def list_files():
#   for project in [glob.glob("/data/analysis/converted/bturner/120626_SN968_0118_AD149JACXX/Unaligned/Project_*")[0]]:
#   	for sample in [glob.glob("%s/*" % project)[0]]:
#		process_sample_directory(sample)

def process_sample_directory(path, read_group, reference, project):
	print "# This Makefile is automatically generated"
	files = glob.glob("%s/*.fastq.gz" % path)
        sample_name = get_sample_name(path)
        if read_group == None:
		read_group = generate_read_group(sample_name)

	print "all: {0}.{1}.recal.filtered.snps.vcf {0}.{1}.clean.dedup.recal.bamqc.out {0}.{1}.snps.R.pdf \n".format(project, sample_name)

	print_clean()
		
	bams = print_bwa(files, read_group, reference)
	print_merge_bams(bams, sample_name)
	print_sort_bam(sample_name)
	print_dpp_bam(sample_name, reference, project)
	print_gatk_genotyper(sample_name, project)
	print_gatk_recalibrate(sample_name, project)
	print_gatk_applyRecal(sample_name, project)
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

def print_bwa(files, read_group, reference):
	for file in files:
                print_bwa_aln_command(file, read_group, reference)
	pairs = group_files(files)
	for pair in pairs:
                print_bwa_sampe_command(pair, read_group, reference)
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
	
def print_bwa_aln_command(file, read_group, reference):
        base    = id_from_path(file) 
	print "\n{0}.sai:".format(base)
	print "\tbwa aln -t 8 -q {0} {1} {2} > {4}.sai ".format(20, reference, file, read_group, base)


def print_bwa_sampe_command(pair, read_group, reference):
        base_r1    = id_from_path(pair[0]) 
        base_r2    = id_from_path(pair[1]) 
	print "\n{0}.bam: {0}.sai {1}.sai".format(base_r1, base_r2)
	print "\tbwa sampe -r '{5}' {0} {1}.sai {2}.sai {3} {4} | samtools view -bhS - > {1}.bam".format(reference, base_r1, base_r2, pair[0], pair[1], read_group)

def print_merge_bams(files, sample_name):
        files = map(lambda x: id_from_path(x) + ".bam", files)
        print "\n%s.bam: %s" % (sample_name, " ".join(files))
	if len(files) == 1:
		print "\tcp %s %s.bam" % ("".join(files), sample_name)
	else:
		print "\tsamtools merge %s.bam %s" % (sample_name, " ".join(files))

def print_sort_bam(sample_name):
        print "\n%s.sorted.bam: %s.bam" % (sample_name, sample_name)
	print "\tsamtools sort %s.bam %s.sorted" % (sample_name, sample_name)

def print_dpp_bam(sample_name, reference, project):
        print "\n%s.%s.clean.dedup.recal.bam: %s.sorted.bam" % (project, sample_name, sample_name)
	print "\tjava -Xmx4g -jar /data1/queue/Queue/Queue.jar -S /data1/queue/qscripts/DataProcessingPipeline.scala -p %s -sg 0 -i %s.sorted.bam -R %s -D /data1/gatk_resources_1_5/dbsnp_135.hg19.vcf.gz -indels /data1/gatk_resources_1_5/1000G_phase1.indels.hg19.vcf.gz -indels /data1/gatk_resources_1_5/Mills_and_1000G_gold_standard.indels.hg19.sites.vcf.gz -tempDir ./tmp -keepIntermediates -startFromScratch -jobReport %s.jobreport -l INFO -run " % (project, sample_name, reference, sample_name)

def print_bam_qc(sample_name, project):
	print "\n%s.%s.clean.dedup.recal.bamqc.out: %s.%s.clean.dedup.recal.bam" % (project, sample_name, project, sample_name)
	print "\trun_bamqc $? > $@"

def print_gatk_genotyper(sample_name, project):
	print "\n%s.%s.raw.snps.vcf: %s.%s.clean.dedup.recal.bam" % (project, sample_name, project, sample_name)
	print "\tjava -Xmx12g -jar $(GATK_TOOL) -T UnifiedGenotyper -nt 8 -dcov 200 -glm SNP -R $(REF) --dbsnp $(DBSNP) -l INFO -o $@ -I $?"

def print_gatk_recalibrate(sample_name, project):
	print "\n{0}.{1}.snps.tranches {0}.{1}.snps.recal {0}.{1}.snps.R: {0}.{1}.raw.snps.vcf".format(project, sample_name)
	print "\tjava -Xmx4g -jar $(GATK_TOOL) -T VariantRecalibrator -R $(REF) -input $? -resource:hapmap,known=false,training=true,truth=true,prior=15.0 $(HAPMAP) -resource:omni,known=false,training=true,truth=false,prior=12.0 $(OMNI) -resource:dbsnp,known=true,training=false,truth=false,prior=6.0 $(DBSNP) -an QD -an HaplotypeScore -an MQRankSum -an ReadPosRankSum -an FS -an MQ -an DP -mode SNP -recalFile {0}.{1}.snps.recal -tranchesFile {0}.{1}.snps.tranches -rscriptFile {0}.{1}.snps.R".format(project, sample_name)
	
def print_r_recalibrate(sample_name, project):
	print "\n {0}.{1}.snps.R.pdf {0}.{1}.snps.tranches.pdf: {0}.{1}.snps.R {0}.{1}.snps.tranches".format(project, sample_name)
	print "\tR CMD BATCH --no-restore --no-save {0}.{1}.snps.R /dev/null".format(project, sample_name)

def print_gatk_applyRecal(sample_name, project):
	print "\n{0}.{1}.recal.filtered.snps.vcf: {0}.{1}.raw.snps.vcf {0}.{1}.snps.tranches {0}.{1}.snps.recal".format(project, sample_name)
	print "\tjava -Xmx4g -jar $(GATK_TOOL) -T ApplyRecalibration -R $(REF) -input {0}.{1}.raw.snps.vcf --ts_filter_level 99.0 -tranchesFile {0}.{1}.snps.tranches -recalFile {0}.{1}.snps.recal -mode SNP -o {0}.{1}.recal.filtered.snps.vcf".format(project, sample_name)

def print_clean():
	print "\nclean:"
	print "\trm -rf *.sai *.bam *.out *.bai *.jobreport *.intervals"
