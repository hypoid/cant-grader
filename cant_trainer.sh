#!/bin/sh

# This generates:
# Trained_models/0/graph.pb
# Trained_models/0/labels.txt
# /tmp/output_labels.txt
# This command is meant to be run from the project's main directory with the following
# structure for subfolders:
#
# Project Dir
#  bottlenecks
#   0
#  Processed_training_data/0
#   0
#    true
#     img1.jpg img2.jpg img3.jpg
#    false
#     img1.jpg img2.jpg img3.jpg

python ~/.envs/cant-grader/tensorflow/tensorflow/examples/image_retraining/retrain.py \
    --image_dir /data/All_training_data/Cant/Processed_cants/1/ \
    --bottleneck_dir=/data/All_training_data/Cant/bottlenecks/1/ \
    --learning_rate=0.0001 \
    --testing_percentage=20 \
    --validation_percentage=20 \
    --train_batch_size=32 \
    --validation_batch_size=-1 \
    --flip_left_right True \
    --flip_up_down False \
    --random_brightness=10 \
    --eval_step_interval=100 \
    --how_many_training_steps=4000 \
    --architecture=mobilenet_1.0_224 \
    --intermediate_store_frequency=100 \
    --intermediate_output_graphs_dir=/data/All_training_data/Cant/Intermediate_graphs/1/ \
    --summaries_dir=/data/All_training_data/Training_logs_for_tensorboard/Cant/ \
    --model_dir=/data/All_training_data/Raw_models
#    --output_graph=/data/All_training_data/Trained_models/Cant/1/graph.pb \
#    --output_labels=/data/All_training_data/Trained_models/Cant/1/labels.txt


#python3 tensorflow/tensorflow/examples/label_image/label_image.py --graph=/tmp/output_graph.pb --labels=/tmp/output_labels.txt --image=/home/rhodes/Desktop/Tracking/middle-not-middle/data/middle/1.jpg --input_layer=input --output_layer=final_result --input_mean=128 --input_std=128 --input_width=128 --input_height=128
