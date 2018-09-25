"""Generate a heatmap of activations for an image."""

import cv2
import argparse
import os
import sys
import traceback
import pdb
import pickle
import glob

import visutil
from detect_cants_and_knots import Box

min_size = 9


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


def bounding_box_area(box):
    return abs(box.xmin-box.xmax)*abs(box.ymin-box.ymax)


sys.excepthook = info

size = 300

ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_folder',
                required=True,
                help='Folder containing scans')
ap.add_argument('-o', '--output_folder',
                required=True,
                help='Folder to store training image')
ap.add_argument('-c', '--camera',
                required=False,
                type=int,
                help='Camera')
args = vars(ap.parse_args())

input_root = args['input_folder']
output_root = args['output_folder']
cam_num = args['camera']

if input_root[-1] is not '/':
    input_root += '/'
if output_root[-1] is not '/':
    output_root += '/'
if not os.path.exists(input_root):
    print('Invalid input folder: {}'.format(input_root))
    exit()
if not os.path.exists(output_root):
    os.mkdir(output_root)
if not os.path.exists(output_root+'empty/'):
    os.mkdir(output_root+'empty/')
if not os.path.exists(output_root+'has_knots/'):
    os.mkdir(output_root+'has_knots/')


scanpaths = glob.glob(input_root+'*/')

filenumber = 1
for scan in scanpaths:
    if cam_num is None:
        imagenames = glob.glob(scan+'*.png')
    else:
        imagenames = ["{}{}.png".format(scan, cam_num)]
    # For each camera image therein
    for imagename in imagenames:
        # If the image isn't annotated with defect bounding boxes
        # then we skip it
        if not os.path.isfile(imagename[:-4]+'.knots'):
            continue

        img = cv2.imread(imagename, -1)
        print('Processing {}'.format(imagename))
        width = img.shape[1]
        height = img.shape[0]

        # Load the defect bounding boxes from disk
        boxes = pickle.load(open(imagename[:-4]+'.knots', 'rb'))

        # Step across the image from left to right, top to bottom 100px
        # at a time and take crops to save as individual files.
        for i in range(int(size/2), width-int(size/2), 100):
            for j in range(int(size/2), height-int(size/2), 100):
                # Crop the image to the current ROI
                y1 = int(j-(size/2))
                y2 = int(j+(size/2))
                x1 = int(i-(size/2))
                x2 = int(i+(size/2))
                crop = img[y1:y2, x1:x2]
                new_boxes = []
                for box in boxes:
                    new_boxes.append(Box(box.ymin-y1,
                                         box.xmin-x1,
                                         box.ymax-y1,
                                         box.xmax-x1))
                # Clamp the boxes to the boundaries of the crop
                for box in new_boxes:
                    if box.xmin < 1:
                        box.xmin = 1
                    if box.xmax < 1:
                        box.xmax = 1
                    if box.ymin < 1:
                        box.ymin = 1
                    if box.ymax < 1:
                        box.ymax = 1
                    if box.xmin > size-1:
                        box.xmin = size-1
                    if box.xmax > size-1:
                        box.xmax = size-1
                    if box.ymin > size-1:
                        box.ymin = size-1
                    if box.ymax > size-1:
                        box.ymax = size-1

                # Filter out the boxes that now have zero width
                new_boxes = [box for box in new_boxes
                             if not box.xmin-box.xmax == 0]
                # Filter out the boxes that now have zero height
                new_boxes = [box for box in new_boxes
                             if not box.ymin-box.ymax == 0]

                # Filter out the boxes that are too small:
                new_boxes = [box for box in new_boxes
                             if bounding_box_area(box) > min_size]

                # If there are no boxes in the view of the crop then
                # we set it aside in a different folder
                if len(new_boxes) == 0:
                    new_path = '{}empty/{}.jpg'.format(output_root,
                                                       filenumber)
                else:
                    new_path = '{}has_knots/{}.jpg'.format(output_root,
                                                           filenumber)
                filenumber += 1

                # Write the files
                visutil.write_image(crop, new_path)
                print("Saving {}".format(new_path))
                with open(new_path[:-4]+'.knots', 'wb') as dump_file:
                    pickle.dump(new_boxes, dump_file)
                    print('Saving {}.knots'.format(new_path[:-4]))
