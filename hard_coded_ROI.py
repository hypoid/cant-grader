"A simple script to gererate a hardcoded ROI list for each camera."

import traceback
import pdb
import sys
import numpy as np
import argparse
import pickle


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info


ap = argparse.ArgumentParser()
ap.add_argument('-p', '--Production',
                required=False,
                type=bool,
                help='Production: True if used for grading')
args = vars(ap.parse_args())
production = args['Production']


cp = np.float32([[[0, 0],
                  [5120, 0],
                  [5120, 448],
                  [0, 448]],
                 [[0, 0],
                  [1280, 0],
                  [1280, 360],
                  [0, 360]],
                 [[0, 0],
                  [1280, 0],
                  [1280, 360],
                  [0, 360]],
                 [[0, 0],
                  [1280, 0],
                  [1280, 360],
                  [0, 360]],
                 [[0, 0],
                  [1280, 0],
                  [1280, 360],
                  [0, 360]]])
small_width = 1280
small_height = 360
big_width = 5120
big_height = 448

ROI_list = []
for cam_num in range(5):
    ROI_list.append([])
for cam_num, cam_list in enumerate(ROI_list):
    if cam_num == 0:
        for i in range(112, 5040, 112):
            for j in range(112, 448, 112):
                cam_list.append([i, j])
    else:
        for i in range(112, 1280, 112):
            for j in range(112, 360, 112):
                cam_list.append([i, j])

if production is True:
    with open("Production_ROI_list.p", 'wb') as ROIfile:
        pickle.dump(ROI_list, ROIfile)
        print("Saving to Production_ROI_list.p")
else:
    with open("ROI_list.p", 'wb') as ROIfile:
        pickle.dump(ROI_list, ROIfile)
        print("Saving to ROI_list.p")
