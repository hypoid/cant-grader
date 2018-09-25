"""Convert scans and bounding boxes to training images.

For each scan folder and camera image in that folder,
create a group of images that are 224x224 that can be used
for training. Store these images in true/false folders per
camera (one folder per camera) inside the output folder.
"""

import cv2
import argparse
import os
import glob
import pickle
import sys
import traceback
import pdb

import visutil


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info


def a_bounding_box_is_in_roi(box_list, roi_point, roi_size):
    """Check if any of the bounding boxes are in the ROI.

    Note: this assumes the 0 point to be the top left corner
    with positive going down and right.
    """
    roi_bottomedge = roi_point[1]+(roi_size/2)
    roi_topedge = roi_point[1]-(roi_size/2)
    roi_leftedge = roi_point[0]-(roi_size/2)
    roi_rightedge = roi_point[0]+(roi_size/2)
    for box in box_list:
        if box.x1 < box.x2:
            box_leftedge = box.x1
            box_rightedge = box.x2
        else:
            box_leftedge = box.x2
            box_rightedge = box.x1
        if box.y2 < box.y1:
            box_bottomedge = box.y1
            box_topedge = box.y2
        else:
            box_bottomedge = box.y2
            box_topedge = box.y1
        if (
            box_bottomedge < roi_bottomedge and
            box_topedge > roi_topedge and
            box_leftedge > roi_leftedge and
            box_rightedge < roi_rightedge
           ):
            if bounding_box_area(box) > 100:
                return True
    return False


def bounding_box_area(box):
    return abs(box.x1-box.x2)*abs(box.y1-box.y2)


DEBUG_DRAWING = False
ROI_list = pickle.load(open('ROI_list.p', 'rb'))
size = 224

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
for i in range(len(ROI_list)):
    path = "{}{}/".format(output_root, i)
    if not os.path.exists(path):
        os.mkdir(path)
    if not os.path.exists(path+'true/'):
        os.mkdir(path+'true/')
    if not os.path.exists(path+'false/'):
        os.mkdir(path+'false/')

scanpaths = glob.glob(input_root+'*/')

per_cam_accum = [0 for camera in ROI_list]

# For each scan folder
for scan in scanpaths:
    if cam_num is None:
        imagenames = glob.glob(scan+'*.png')
    else:
        imagenames = ["{}{}.png".format(scan, cam_num)]
    # For each camera image therein
    for imagename in imagenames:
        # If the image isn't annotated with defect bounding boxes
        # then we skip it
        if not os.path.isfile(imagename+'.knots'):
            continue

        # Get the camera number from the file name
        camera_number = int(imagename[-5:-4])

        print('Processing {}'.format(imagename))
        # Load the image from disk
        img = cv2.imread(imagename, -1)
        work_img = img.copy()

        # Load the defect bounding boxes from disk
        boxes = pickle.load(open(imagename+'.knots', 'rb'))

        # For each ROI of that camera
        for point in ROI_list[camera_number]:
            # Crop the image to the current ROI
            x = point[0]
            y = point[1]
            y1 = int(y-(size/2))
            y2 = int(y+(size/2))
            x1 = int(x-(size/2))
            x2 = int(x+(size/2))
            crop = img[y1:y2, x1:x2]
            per_cam_accum[camera_number] += 1
            if a_bounding_box_is_in_roi(boxes, point, size):
                # save to 'False'
                path = "{}{}/false/{}.jpg".format(output_root,
                                                  camera_number,
                                                  per_cam_accum[camera_number])
                print('Saving {}'.format(path))
                visutil.write_image(crop, path)
                if DEBUG_DRAWING:
                    cv2.rectangle(work_img,
                                  (point[0]-int(size/2), point[1]-int(size/2)),
                                  (point[0]+int(size/2), point[1]+int(size/2)),
                                  (0, 0, 255),
                                  2)
            else:
                # save to 'True'
                path = "{}{}/true/{}.jpg".format(output_root,
                                                 camera_number,
                                                 per_cam_accum[camera_number])
                print('Saving {}'.format(path))
                visutil.write_image(crop, path)
                if DEBUG_DRAWING:
                    cv2.rectangle(work_img,
                                  (point[0]-int(size/2), point[1]-int(size/2)),
                                  (point[0]+int(size/2), point[1]+int(size/2)),
                                  (0, 255, 0),
                                  2)
        if DEBUG_DRAWING:
            for box in boxes:
                cv2.rectangle(work_img,
                              (box.x1, box.y1),
                              (box.x2, box.y2),
                              (0, 255, 255),
                              1)
            cv2.imshow('image',
                       work_img)
            k = cv2.waitKey(0) & 0xFF
            if k == 27:
                print("Operation Canceled By User")
                exit()
