#!/bin/bash
killall python
killall python3
cd /home/spfpe/cant-grader
# echo "python3 GRADE.py" > initfile
/usr/bin/gnome-terminal -- bash --init-file initfile -i
