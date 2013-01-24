#!/usr/bin/perl -w

use strict;
use warnings;

if ($#ARGV < 2)
{
	print "This tool takes the initial coverage summary file and adds annotations to it (Gene Name and Exon Name)\n";
	print "Usage format_coverage.pl <Coverage_Interval_Summary> <RefGene> <RefSeq.Exon>\n";
	exit;
}

#my $refGene = "/data1/genelists/refGene.broad.sorted.txt";
#my $refExon = "/data1/regions/refSeq.exon.sorted.bed"; # Or a selected interval list

my $coverage = $ARGV[0];
my $refGene = $ARGV[1];
my $refExon = $ARGV[2];

open (REFGENEFILE, $refGene) or die($!);
open (REFEXONFILE, $refExon) or die($!);
open (COVERAGEFILE, $coverage) or die($!);
 
my %refGene = ();
my %refExon = ();

while(my $line = <REFGENEFILE>) {
	chomp($line);
	
	my @col = split(' ', $line);

	my $refSeqID = $col[1];
	my $geneName = $col[12];

	$refGene{"$refSeqID"}="$geneName";
}

while(my $line = <REFEXONFILE>) {
	chomp($line);
	my @col = split(' ', $line);

	my $chr = $col[0];
	my $startPos = $col[1]; # Need to add a +1 if using GATK
	my $endPos = $col[2];
	my $exonID = $col[3];
	
	my $chrPos = "$chr:$startPos-$endPos";
	
	$exonID =~ m/(NM|NR)_(.+?)_(.+?)_chr.+/;
	
	my $refGeneID = $1 . "_" . $2;
	my $exonName = $3;
	my $geneName = "unknown";

	if (exists $refGene{"$refGeneID"}) {
		$geneName = $refGene{"$refGeneID"};
	}	

	$refExon{"$chrPos"} ="$geneName\t$refGeneID\t$exonName";
		
}

while(my $line = <COVERAGEFILE>) {
	chomp($line);
	
	if ($line =~ m/(chr.+?):(.+?)-(.+?)\t(.+)/) #$1 = chromosom $2 = startPos $3 = endPos $4 = coverageStats
	{
		if(exists $refExon{"$1:$2-$3"}) {
			my $exonInfo = $refExon{"$1:$2-$3"};
	        	$line = "$exonInfo\t$1\t$2\t$3\t$4"; #exonInfo contains: "GeneName  RefGeneID  ExonName" and is retrieved by chromosom position
		}
		else
		{
			$line = "unknown\tunknown\tunknown\t$1\t$2";
#			$unmatched = $unmatched + 1;
		}
	}
	else
	{
		$line = "gene\trefSeq\texon\tchr\tstartPos\tendPos\ttotal\tavg\tsample.total\tsample.avg\tmin\tq1\tmedian\tq3\tpct\>15\tpct\=0";
	}	

	print "$line\n";
}


close (REFEXONFILE) or die ($!);
close (COVERAGEFILE) or die ($!);
close (REFGENEFILE) or die ($!);
