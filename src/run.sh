#!/bin/bash

: > board.txt 

while getopts "cpt:rd" opt; do
  case ${opt} in
    c)  echo "Clearing logs" 
        rm -rf ../logs/*.log
        ;;
    p)  echo "Clearing pickles"
        rm -rf ../pkl/*.pkl
        ;;
    t)  echo "Running test number ${OPTARG}"
        python3 __main__.py --test ${OPTARG}
        ;;
    r)  echo "Reloading demo from last time"
        python3 __main__.py --reload
        ;;
    d)  echo "Running full demo"
        python3 __main__.py --demo 1
        : > board.txt 
        python3 __main__.py --demo 2
        : > board.txt 
        python3 __main__.py --demo 3
        : > board.txt 
        python3 __main__.py --demo 4
        ;;
    \?) echo "Usage: cmd [-c] [-t] [-d]"
        ;;
  esac
done

rm board.txt
