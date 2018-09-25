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


def cant_is_centered(box_list, roi_point, roi_size):
    """Check if any of the bounding boxes are in the ROI.

    Note: this assumes the 0 point to be the top left corner
    with positive going down and right.
    """
    for box in box_list:
        if box.y2 < box.y1:
            box_topedge = box.y2
        else:
            box_topedge = box.y1
        midbox = box_topedge + int(abs(box.y1-box.y2)/2)
        if abs(midbox-roi_point[1]) < 15:
            return True
    return False


def bounding_box_area(box):
    return abs(box.x1-box.x2)*abs(box.y1-box.y2)


DEBUG_DRAWING = False
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
for i in range(5):
    path = "{}{}/".format(output_root, i)
    if not os.path.exists(path):
        os.mkdir(path)
    if not os.path.exists(path+'true/'):
        os.mkdir(path+'true/')
    if not os.path.exists(path+'false/'):
        os.mkdir(path+'false/')

scanpaths = glob.glob(input_root+'*/')

per_cam_accum = [0 for camera in range(5)]

# For each scan folder
for scan in scanpaths:
    if cam_num is None:
        imagenames = glob.glob(scan+'*.png')
    else:
        imagenames = ["{}{}.png".format(scan, cam_num)]
    # For each camera image therein
    for imagename in imagenames:
        # If the image isn't annotated with bounding boxes
        # then we skip it
        if not os.path.isfile(imagename+'.cants'):
            continue

        # Get the camera number from the file name
        camera_number = int(imagename[-5:-4])

        print('Processing {}'.format(imagename))
        # Load the image from disk
        img = cv2.imread(imagename, -1)
        work_img = img.copy()

        # Load the defect bounding boxes from disk
        boxes = pickle.load(open(imagename+'.cants', 'rb'))
        height = img.shape[0]
        pointlist = []
        for j in range(int(size/2), height-int(size/2), 1):
            pointlist.append([size/2, j])

        # For each ROI of that camera
        for point in pointlist:
            # Crop the image to the current ROI
            x = point[0]
            y = point[1]
            y1 = int(y-(size/2))
            y2 = int(y+(size/2))
            x1 = 0
            x2 = img.shape[1]
            crop = img[y1:y2, x1:x2]
            per_cam_accum[camera_number] += 1
            if not cant_is_centered(boxes, point, size):
                # save to 'False'
                path = "{}{}/false/{}.jpg".format(output_root,
                                                  camera_number,
                                                  per_cam_accum[camera_number])
                print('Saving {}'.format(path))
                resize = cv2.resize(crop,
                                    (size, size),
                                    interpolation=cv2.INTER_LINEAR)
                visutil.write_image(resize, path)
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
