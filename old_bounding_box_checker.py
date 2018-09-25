"""Lable the designated folder of scans."""

import cv2
import argparse
import os
import glob
import pickle
import numpy as np

import visutil
import detect_cants_and_knots


def mouse_handler(event, x, y, flags, param):
    """Update the mouse position as mouse move events call this function."""
    global mouseX, mouseY, Clicked, Unclicked
    if event == cv2.EVENT_MBUTTONDOWN:
        Clicked = True
        mouseX, mouseY = x, y
    if event == cv2.EVENT_MBUTTONUP:
        Unclicked = True
        mouseX, mouseY = x, y
    elif event == cv2.EVENT_MOUSEMOVE:
        mouseX, mouseY = x, y


mouseX, mouseY = 100, 100
Clicked = False
Draw_current = False
Unclicked = False
current_box = visutil.bounding_box(mouseX,
                                   mouseY,
                                   mouseX,
                                   mouseY)
cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
cv2.setMouseCallback('image', mouse_handler)

ap = argparse.ArgumentParser()
ap.add_argument('-f', '--folder',
                required=True,
                help='Folder containing scans')
args = vars(ap.parse_args())
root = args['folder']

if root[-1] is not '/':
    root += '/'
if not os.path.exists(root):
    print('Invalid root: {}'.format(root))
    exit()
all_images = glob.glob(root+'*/*.png')
all_images += glob.glob(root+'*/*.jpg')

immediate_dir_images = glob.glob(root+'*.png')
immediate_dir_images += glob.glob(root+'*.jpg')

if len(immediate_dir_images) > len(all_images):
    all_images = immediate_dir_images
    all_filenames = [x for x in all_images if os.path.isfile(x[:-4]+'.knots')]

# Filter out images that have already been checked
filenames = [x for x in all_filenames if not os.path.isfile(
    x[:-4]+'.knots.checked')]
if not len(all_filenames) == 0:
    print("{}% Done".format(100-(len(filenames)/len(all_filenames))))
else:
    print("No bounding boxes to check!")
    exit()
if filenames == []:
    print("All .knots files checked. Exiting")

# For each scan's file, allow the user to place bounding boxes
for filename in filenames:
    print("Opening {} to check annotations".format(filename))
    img = cv2.imread(filename, -1)
    start_new = True
    list_of_boxes = pickle.load(open(filename[:-4]+'.knots', 'rb'))
    while True:
        work_img = img.copy()
        for box in list_of_boxes:
            cv2.rectangle(work_img,
                          (box.x1, box.y1),
                          (box.x2, box.y2),
                          (0, 255, 255),
                          2)
        if Draw_current is True:
            current_box.x2 = mouseX
            current_box.y2 = mouseY
            cv2.rectangle(work_img,
                          (current_box.x1, current_box.y1),
                          (current_box.x2, current_box.y2),
                          (0, 255, 0),
                          2)
        cv2.line(work_img,
                 (mouseX, mouseY),
                 (mouseX + 50, mouseY),
                 (0, 255, 255),
                 2)
        cv2.line(work_img,
                 (mouseX, mouseY),
                 (mouseX, mouseY + 50),
                 (0, 255, 255),
                 2)
        cv2.imshow('image', work_img)
        k = cv2.waitKey(1) & 0xFF
        if k == 101:
            if len(list_of_boxes) > 0:
                list_of_boxes.pop(-1)
        if k == 27:
            print('Operation Canceled By User')
            exit()
        elif k == 13:
            with open(filename+'.checked', 'wb') as file_to_dump_into:
                pickle.dump(' ', file_to_dump_into)
                print(filename+'.checked written')
            with open(filename[:-4]+'.knots', 'wb') as file_to_dump_into:
                pickle.dump(list_of_boxes, file_to_dump_into)
                print(filename[:-4]+'.knots re-written')
            break
        if Clicked is True:
            Clicked = False
            Draw_current = True
            current_box = visutil.bounding_box(mouseX,
                                               mouseY,
                                               mouseX,
                                               mouseY)
        if Unclicked is True:
            Draw_current = False
            Unclicked = False
            current_box.x2 = mouseX
            current_box.y2 = mouseY
            list_of_boxes.append(current_box)
cv2.destroyAllWindows()
