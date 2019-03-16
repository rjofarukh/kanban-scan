#!/bin/bash

: > ../live_view/board.txt 

rm ../data/basic/.DS_Store &>/dev/null
rm ../data/correcting_movement/.DS_Store &>/dev/null
rm ../data/assignees/.DS_Store &>/dev/null
FOLDER=""

# run the mongodb server

#mongod --dbpath ~/projects/kanban-scan/db &

# command to remove all the logs except for the last 10

while getopts "f:cpt:rd" opt; do
  case ${opt} in
    f)  FOLDER=${OPTARG}
        ;;
    c)  echo "Clearing logs" 
        rm -rf ../logs/*.log
        ;;
    p)  echo "Clearing pickles"
        rm -rf ../pkl/*.pkl
        ;;
    t)  echo "Running test number ${OPTARG}"
        python3 __main__.py --test ${OPTARG} --folder "$FOLDER" #&& fg
        ;;
    r)  echo "Reloading demo from last time"
        python3 __main__.py --reload
        ;;
    d)  echo "Running full demo"
        echo "Running basic sequence"
        python3 __main__.py --demo 1 --folder "../data/basic/" #&& fg
        : > ../live_view/board.txt 
        echo "Running correcting_movement sequence"
        python3 __main__.py --demo 1 --folder "../data/correcting_movement" #&& fg
        : > ../live_view/board.txt 
        echo "Running assignee sequence"
        python3 __main__.py --demo 1 --folder "../data/assignees" #&& fg
        ;;
    \?) echo "Usage: cmd [-f] folder [-c] clear logs [-p] clear pickes [-t] test [-d] demo"
        ;;
  esac
done
