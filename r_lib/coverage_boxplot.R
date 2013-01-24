args=(commandArgs(TRUE))
print(args)

#Read in coverage data from file
covData = read.table(args[1], header=T, sep="\t", row.names=NULL)
geneName = covData[,1]
exonName = covData[,3]
startPos = covData[,5]
endPos = covData[,6]
q1=covData[,12]
q2=covData[,13]
q3=covData[,14]
covStats=covData[,11:15]

#The numver of Observations (numObs) can ideally estimated by total_coverage / average_coverage --> yielding number of bases (observations)
#However, the exact number is not needed since it is only used for confidence interval to display outliers (which we don't)
numObs=endPos-startPos

#For each row in coverage data, 
#for (i in 1:nrow(covData)) {

        outFolder = args[2]
	fileName = paste(outFolder, "/", geneName[1], ".plot.pdf", sep = "")

	#conf is calculated as: median +/- 1.58 * (Q3-Q1) / sqrt(n)
    	confMin = q2 - 1.58 * (q3 - q1) / sqrt(numObs)
    	confMax = q2 + 1.58 * (q3 - q1) / sqrt(numObs)

	#This list is the format required by the bxp command
	confSum = list(stats=t(covStats), n=numObs, conf=t(matrix(c(confMin,confMax), nrow=nrow(covData), ncol=2)), out=numeric(0), group=numeric(0), names=exonName)


	#confSum
	#fileName
	#geneName[1]

	pdf.options()

	#Plot and save to PDF
	pdf(fileName, width=10, height=7)
		bxp(confSum, main=geneName[1], ylab="Depth of Coverage for Sample - with PCR duplicates", las=2, cex.lab=1, cex.axis=0.7)
		abline(h=20, lty=2, col="red")
	dev.off()
#}
