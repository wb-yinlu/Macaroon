#!/bin/sh

pybin=python2.7

echo "|CaseYaml|: "$1
casename=${1%.yaml*}

casename="$casename.py"
echo "|TestCase|: "$casename

data2case="data2case.py"
casename="$casename"

echo '|CaseTranslate|: '
echo "$pybin $data2case $1"
$pybin $data2case $1

echo '|CaseRun|: '
echo "$pybin $casename"
$pybin $casename

rm -f $casename
