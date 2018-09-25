
"""Select regions of interest and save them to disk.

Each camera needs its own set of ROI boxes. This is done
by constructing a list of lists that is shaped accordingly:
NUMBER_OF_CAMERAS X NUMBER_OF_BOXES. This list is saved in
a file called ROI_list.p
"""

import os
import cv2
import pickle
import glob
import argparse
import traceback
import pdb
import sys
import numpy as np


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info


def mouse_handler(event, x, y, flags, param):
    """Update the mouse position as mouse move events call this function."""
    global mouseX, mouseY, points_clicked_status, window_point_list, SCALE
    x, y = x*SCALE, y*SCALE
    if event == cv2.EVENT_MBUTTONDOWN:
        mouseX, mouseY = x, y
        for index, point in enumerate(window_point_list):
            dist = (point[0]-x)*(point[0]-x)+(point[1]-y)*(point[1]-y)
            if dist < 400:
                points_clicked_status[index] = True
    elif event == cv2.EVENT_MBUTTONUP:
        mouseX, mouseY = x, y
        points_clicked_status = [False, False, False, False]
    elif event == cv2.EVENT_MOUSEMOVE:
        mouseX, mouseY = x, y
        for index, point in enumerate(window_point_list):
            if points_clicked_status[index] is True:
                window_point_list[index] = [x, y]


ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_image',
                required=True,
                help='Folder containing a set of camera images')
ap.add_argument('-o', '--output_file_name',
                required=True,
                help='File name to save ROI to.')
args = vars(ap.parse_args())
input_image = args['input_image']
output_filename = args['output_file_name']

if not os.path.isfile(input_image):
    print('Invalid input image: {}'.format(input_image))
    exit()
img = cv2.imread(input_image, -1)


window_point_list = np.float32([[172,1756],
                                [3340,1],
                                [3584,384],
                                [188,2064]])
points_clicked_status = [False, False, False, False]

cv2.namedWindow('image')
cv2.setMouseCallback('image', mouse_handler)

SCALE = 4
mouseX = 100
mousey = 100
Clicked = False
img = cv2.imread(input_image, -1)

while True:
    work_img = img.copy()
    for point in window_point_list:
        cv2.circle(work_img,
                   (point[0], point[1]),
                   10,
                   (50, 50, 255),
                   -1)
    cv2.imshow('image',
               work_img[::SCALE, ::SCALE, :])
    k = cv2.waitKey(1) & 0xFF
    if k == 27:
        print("Operation Canceled By User")
        exit()
    elif k == 13:
        break

correct_points = np.float32([[0,0],
                             [5120,0],
                             [5120,448],
                             [0,448]])
M = cv2.getPerspectiveTransform(window_point_list, correct_points)
corrected_image = cv2.warpPerspective(img,M,(5120,448))

cv2.imshow('image', corrected_image)# [::SCALE, ::SCALE, :])
k = cv2.waitKey(0) & 0xFF

cv2.destroyAllWindows()
print("Saving to {}".format(output_filename))
with open(output_filename, 'wb') as ROIfile:
    pickle.dump(window_point_list, ROIfile)
