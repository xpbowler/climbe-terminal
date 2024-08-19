#!/usr/bin/env bash
echo "Run Match"
defaultAlgo=$PWD/bluecheese
anotherAlgo=$PWD/cheese-v2

algo1=${1:-${defaultAlgo}}
algo1=${algo1%/}
algo2=${2:-${anotherAlgo}}
algo2=${algo2%/}

echo "P1: ${algo1}"
echo "P2: ${algo2}"
echo "Starting Match: ${algo1} vs. ${algo2}"
java -jar engine.jar work ${algo1}/run.sh ${algo2}/run.sh
