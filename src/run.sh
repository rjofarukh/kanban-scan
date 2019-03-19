#!/bin/bash

##################################################################
#
# To use :
#   python3 -m pip install --user virtualenv
#   python3 -m virtualenv $environment_name
#   source $environment_name/bin/activate
#   pip install -r requirements.txt
#
# After you're done : 
#   deactivate    # deactivates the environment
#

# Make sure you have all the requirements from requirements.txt
# 
# Most important ones are: 
#   opencv, tensorflow, keras, scikit-learn, scikit-image, todoist-python, pymongo,
#   pyzbar, terminaltables, matplotlib
#
#

# Firstly, run db_start.sh to launch the actual database
# Optionally, then run watch.sh to see the current state
# of the board along with any pictures you like 
# (hold CMD + picture_path to open the picture in preview)
# 
# Then launch ./run -d to run the full demo, -t is just for testing
# and prints logging.debug
#
# 
#
: > ../live_view/board.txt 

rm ../data/basic/.DS_Store &>/dev/null
rm ../data/correcting_movement/.DS_Store &>/dev/null
rm ../data/assignees/.DS_Store &>/dev/null
FOLDER=""



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
