#!/bin/bash

#input args is project-name formula result.txt/result_orignal.txt
cur=`pwd`
project=$1
formula=$2
count=1

for g in Op2 Jaccard Ochiai Wong2 Ochiai2 Tarantula;
do
	count=$[$count+2]
	if [ $formula = $g  ];
	then
		break
	fi	
done
echo 'the count is '$count

fileName=$3
wd=${cur}/gzoltars/${project}
cd $wd

for sub in `ls`;
do
	if [ -e $wd/${sub}/$fileName ];
	then
		f=$wd/${sub}/$fileName
		outputFile=${f}_$formula
		if [ -e $outputFile ];
		then
			rm $outputFile
		fi
		cat $f |gawk -F '[,#]' '{print $1,$'$count'|"sort -n -r -k 2"}'>$outputFile
	fi
done
