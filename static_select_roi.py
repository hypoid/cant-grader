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


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info


def mouse_handler(event, x, y, flags, param):
    """Update the mouse position as mouse move events call this function."""
    global mouseX, mouseY, ROI_list, camera_number
    if event == cv2.EVENT_MBUTTONDOWN:
        mouseX, mouseY = x, y
        ROI_list[camera_number].append([x, y])
    elif event == cv2.EVENT_MOUSEMOVE:
        mouseX, mouseY = x, y


ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_scan_folder',
                required=True,
                help='Folder containing a set of camera images')
ap.add_argument('-o', '--output_file_name',
                required=True,
                help='File name to save ROI to.')
args = vars(ap.parse_args())
input_folder = args['input_scan_folder']
output_filename = args['output_file_name']

if input_folder[-1] is not '/':
    input_folder += '/'
if not os.path.exists(input_folder):
    print('Invalid input folder: {}'.format(input_folder))
    exit()
camera_image_files = glob.glob(input_folder+'*.png')

size = 224
ROI_list = [[] for _ in camera_image_files]
mouseX, mouseY = 100, 100
camera_number = 0
cv2.namedWindow('image')
cv2.setMouseCallback('image', mouse_handler)
wide_camera_cal = pickle.load(open('wide_camera_cal.p', 'rb'))

for image_file in camera_image_files:
    img = cv2.imread(image_file, -1)
    camera_number = int(image_file[-5:-4])
    while True:
        work_img = img.copy()
        cv2.rectangle(work_img,
                      (mouseX-int(size/2), mouseY-int(size/2)),
                      (mouseX+int(size/2), mouseY+int(size/2)),
                      (0, 255, 255),
                      4)
        for point in ROI_list[camera_number]:
            cv2.rectangle(work_img,
                          (point[0]-int(size/2), point[1]-int(size/2)),
                          (point[0]+int(size/2), point[1]+int(size/2)),
                          (0, 0, 255),
                          4)
        cv2.imshow('image',
                   work_img)
        k = cv2.waitKey(1) & 0xFF
        if k == 101:
            if len(ROI_list[camera_number]) > 0:
                ROI_list[camera_number].pop(-1)
        if k == 27:
            print("Operation Canceled By User")
            exit()
        elif k == 13:
            break
cv2.destroyAllWindows()

print("Saving to {}".format(output_filename))
with open(output_filename, 'wb') as ROIfile:
    pickle.dump(ROI_list, ROIfile)
