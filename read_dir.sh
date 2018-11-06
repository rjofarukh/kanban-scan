#!/bin/bash

########################################################################
#
# If the folder has 5 photos or less, use them all for thresholding and 
# print them all into the photo list file
# 
# Else, use the newest 2 photos to check for differences
#
# Run the loop every time the number of files in the directory starting
# with IMG* goes up
#
########################################################################
trim() {
    local temp="$1"

    temp="${temp#"${temp%%[![:space:]]*}"}"
    temp="${temp%"${temp##*[![:space:]]}"}"

    echo -n "$temp"
}

########################################################################

SLEEP="0.5"
PHOTO_LIST_FILE="photos.txt"
INIT_NUM_FILES="3"
INITIATED="FALSE"
#/Users/rjofarukh/Google Drive/

if [[ $# -eq 0 ]]; then 
  printf "Please supply an argument representing the root folder of your cloud service\n"
  exit 1
fi

if [[ ! -d "$1" ]]; then 
  printf "Please supply a valid directory representing the root folder of your cloud service\n"
  exit 1
fi

# Finds the most recent folder which is going to contain the screenshots 
# Needs to be done only once, the folder shouldn't change while the program runs
FOLDER=$(find "$1" -type d -name "Photo\ Lapse*" | sort -r | head -1)

NUM_FILES=0

while true ; do 

  PREV_NUM_FILES=$NUM_FILES
  NUM_FILES=$(ls "$FOLDER" | wc -l)
  NUM_FILES=$(trim $NUM_FILES)

  if [[ $PREV_NUM_FILES -ne $NUM_FILES ]]; then
    if [[ $INITIATED -eq "FALSE" && $NUM_FILES -ge "3" ]]; then
        find "$FOLDER" -name "IMG*.jpg" | sort -r | head -"$NUM_INIT_FILES" > "$PHOTO_LIST_FILE"        
        # Start initiation program
        echo "INITIATION"
        INITIATED="TRUE"
    elif [[ "INITIATED" = "TRUE" ]]; then
      find "$FOLDER" -name "IMG*.jpg" | sort -r | head -1 > "$PHOTO_LIST_FILE"
      echo "MAIN"
      # start main program
    fi
  fi

  echo "PREV = $PREV_NUM_FILES"
  echo "CURR = $NUM_FILES"
  sleep $SLEEP
done