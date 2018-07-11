#!/bin/bash

#if [ $# -eq 0 ] || [ $# -eq 1 ]; then
#  	echo "Usage: $0 [\"command\"] [file]"
#  	exit 0
#fi 
if [ $# -eq 0 ] ; then
  	echo "Usage: $0 [\"command\"]"
  	exit 0
fi 
   
# for i in $(seq 1 16); do
for i in 9 12 13 14 15 16 ; do
  ssh pi@rasp"${i}" -t "sudo /sbin/ifconfig wlan0 10.0.0.${i} netmask 255.255.255.0"
done
#file="$2"
#while IFS= read line
#do
#  echo $line
#  ssh pi@"${line}" -t "${1}"
#done < "$file"
