#!/bin/bash
source /home/ubuntu/.envs/cant-grader/bin/activate
export PYTHONPATH=$PYTHONPATH/home/ubuntu/.envs/cant-grader/tensorflow/models/research:/home/ubuntu/.envs/cant-grader/tensorflow/models/research/slim:/home/ubuntu/chrono_build/bin
cd /home/ubuntu/cant-grader
/usr/bin/gnome-terminal --command 'bash -i -c "python GRADE.py"'
