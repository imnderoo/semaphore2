import os, time, sys
import glob, re

THREADS=8

def read_file(sample, read):
	return "%s_R%s.fastq.gz" % (sample, read)

def tophat(samples, path, reference):
	for sample in samples:
		print "%s_thout:" % sample
		print "\ttophat -p %s %s.gtf -o %s_thout %s %s" % (THREADS, reference, sample, read_file(sample, 1), read_file(sample,2))

def cufflinks(samples, path):
	for sample in samples:
		print "%s_clout: %s_thout" % (sample, sample)
		print "\tcufflinks -p %s -o %s_clout %s_thout/accepted_hits.bam" % (THREADS, sample, sample)
		print "\techo './%s_clout/transcripts.gtf' >> assemblies.txt" % sample

def cufflink_output(samples1, samples2):
	return " ".join(map(lambda x: "./%s_clout/transcripts.gtf" % x, (samples1 + samples2)))

def tophat_output(samples1):
	return ",".join(map(lambda x: "./%s_thout/accepted_hits.bam" % x, samples1))


def cuffmerge(samples1, samples2, reference):
	print "merged_asm/merged.gtf: %s" % cufflink_output(samples1, samples2)
	print "\tcuffmerge -g %s.gtf -s %s.fa -p %s assemblies.txt" % (reference, reference, THREADS)

def cuffdiff(name1, name2, samples1, samples2, reference):
	print "diff_out: merged_asm/merged.gtf"
	print "\tcuffdiff -o diff_out -b %s.fa -p %s -L %s,%s -u merged_asm/merged.gtf %s %s" % (reference, THREADS, name1, name2, tophat_output(samples1), tophat_output(samples2))

def cummeRbund():
	print "analysis.txt: diff_out"
	print "\t# To be implemented" 

def rna_seq_makefile(name1, name2, samples1, samples2, reference, data_path):
	print "# This Makefile is automatically generated"
	print "GENE_FILE=%s.gtf" % reference
	print "REFERENCE=%s" % reference
	print ""
	print "all: plot"
	print "#### Tophat ####"
	tophat(samples1, data_path, reference)	
	tophat(samples2, data_path, reference)
	print ""
	print "### Cufflinks ###"
	cufflinks(samples1, data_path)
	cufflinks(samples2, data_path)
	print ""
	print "### Cuffmerge ###"
	cuffmerge(samples1, samples2, reference)
	print ""
	print "### Cuffdiff ###"
	cuffdiff(name1, name2, samples1, samples2, reference)
	print ""
	print "### R commands ###"
	cummeRbund()


### Target output
# GENE_FILE=genes.gtf
# REFERENCE=genome
#
# all: plot
# 
# clean:
#	rm -rf C1_R1_thout C1_R1_clout diff_out
#
# C1_R1_thout:
#	echo "tophat -p 8 $(GENE_FILE) -o C1_R1_thout $(REFERENCE) C1_R1_1.fq C1_R1_2.fq"
#
#
# C1_R1_clout: C1_R1_thout
#	echo "cufflinks -p 8 -o C1_R1_clout C1_R1_thout/accepted_hits.bam"
#	echo "C1_R1_clout/transcripts.gtf >> assemblies.txt"
#
# diff_out: C1_R1_clout
#	echo "cuffdiff -o diff_out -b $(REFERENCE).fa -p 8 -L C1,C2 -u merged_asm/merged.gtf C1_R1_thout/accepted_hits.bam C2_R1_thout/accepted_hits.bam"
#
# plot: diff_out  
