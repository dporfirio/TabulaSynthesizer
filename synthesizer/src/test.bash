#!/bin/bash

verbose="False"
reset_oracle=""
while getopts "rv" arg; do
  case $arg in
    r)
      reset_oracle="reset" 
      ;;
    v)
      verbose="True"
      ;;
  esac
done

FILES=../test_data/0.1/*

count=0
corr_count=0

for f in $FILES; do
	if [[ $reset_oracle == "reset" ]]; then
		python3 pipeline.py -f $f -o > out.txt
	else
		python3 pipeline.py -f $f > out.txt
		bn=`basename $f`
		ofile="./test_files/oracle/${bn}.txt"
		tfile="./test_files/temp/${bn}.txt"
		d=`diff $ofile $tfile`
		if [[ $d == "" ]]; then
			echo PASSED test $bn
			corr_count=$(($corr_count+1))	
		else
			echo FAILED test $bn
			cat out.txt >> err.txt
		fi
		if [[ $verbose == "True" ]]; then
			echo "======verbose output========"
			cat "./test_files/temp/${bn}.txt"
			echo
			echo
		fi
		count=$(($count+1))
	fi
done

echo RESULT: $corr_count out of $count tests passed.

if [[ $corr_count == $count ]]; then
	echo Great job!
fi