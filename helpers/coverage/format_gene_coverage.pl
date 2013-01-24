#!/usr/bin/perl -w

use strict;
use warnings;

if ($#ARGV < 2)
{
	print "This tool parses through the coverage summary and extract the coverage stats for each gene in the gene list.\n";
	print "Usage format_coverage.pl <coverage_summary> <gene_list> <output_directory>\n";
	exit (1);
}

my $coverage = $ARGV[0];
my $geneListFile = $ARGV[1];
my $outDir = $ARGV[2];

open (COVERAGEFILE, $coverage) or die($!);
open (GENELIST, $geneListFile) or die($!);

mkdir "$outDir" unless (-d $outDir);

my %geneList = ();

while(my $line = <GENELIST>) {
	chomp($line); #each line is a geneName
	
	#print $line;
	my $fh;
	open ($fh, ">$outDir/$line.txt") or die $!;
	print $fh "gene\trefSeq\texon\tchr\tstartPos\tendPos\ttotal\tavg\tsample.total\tsample.avg\tmin\tq1\tmedian\tq3\tmax\tpctGT15\tpctEQ0\n"; #Print header
	$geneList{$line}=$fh;
}


while(my $line = <COVERAGEFILE>) {
	chomp($line);
	
	if ($line =~ m/(.+?)\t.+/) {
		my $geneName = $1;

	#	print $geneName . "\n";
		
		if (exists($geneList{$geneName})) {
			print {$geneList{$geneName}} "$line\n"; 
		}
	}
	
}

close $_ foreach values %geneList or die ($!);
close (COVERAGEFILE) or die ($!);
close (GENELIST) or die ($!);
