#!/bin/bash

if [ $# -lt 1 ]; then
	echo "This script uses the linux sort function to sort and deduplicate .BED files"
	echo "Usage: $(basename $0) <.BED file>"
	exit
fi

infile=$(readlink -f $1)

sort -k1,1 -k2,2n -k3,3n -u $infile > $(dirname $infile)/$(basename $infile .bed).sort.dedup.bed

