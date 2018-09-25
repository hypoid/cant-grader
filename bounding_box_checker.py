"""Lable the designated folder of scans."""

import cv2
import argparse
import os
import glob
import pickle
import traceback
import pdb
import sys
import numpy as np

from detect_cants_and_knots import Box


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


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


def delete_closest(boxes, x, y):
    dist = []
    for box in boxes:
        box_center = ((box.xmin+box.xmax)/2, (box.ymin+box.ymax)/2)
        dist.append(rel_dist(box_center, (x, y)))
    if len(boxes) > 0:
        lowest_dist_index = 0
        for i, d in enumerate(dist):
            if dist[i] < dist[lowest_dist_index]:
                lowest_dist_index = i
        boxes.pop(lowest_dist_index)


def rel_dist(point1, point2):
    return (point1[0]-point2[0])**2+(point1[1]-point2[1])**2


DEBUG = True
if DEBUG:
    sys.excepthook = info
mouseX, mouseY = 100, 100
Clicked = False
Draw_current = False
Unclicked = False
current_box = Box(mouseY,
                  mouseX,
                  mouseY,
                  mouseX)
cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
cv2.setMouseCallback('image', mouse_handler)

ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_folder',
                required=True,
                help='Folder containing scans')
ap.add_argument('-t', '--filetype',
                required=True,
                help='File extension to look for, e.g. .knots or .cant')
args = vars(ap.parse_args())
root = args['input_folder']
ftype = args['filetype']

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
    all_filenames = [x for x in all_images if os.path.isfile(x[:-4]+ftype)]
else:
    all_filenames = [x for x in all_images if os.path.isfile(x[:-4]+ftype)]


# Filter out images that have already been checked
filenames = [x for x in all_filenames if not os.path.isfile(
    x[:-4]+ftype+'.checked')]
if not len(all_filenames) == 0:
    print("{}% Done".format((len(filenames)/len(all_filenames))))
    print('{}/{}'.format(
        len(all_filenames)-len(filenames), len(all_filenames)))
else:
    print("No bounding boxes to check!")
    exit()
if filenames == []:
    print("All {} files checked. Exiting".format(ftype))

# For each scan's file, allow the user to place bounding boxes
fidx = 0
while fidx < len(filenames) and fidx > -1:
    print("Opening {} to check annotations".format(filenames[fidx]))
    img = cv2.imread(filenames[fidx], -1)
    list_of_boxes = pickle.load(open(filenames[fidx][:-4]+ftype, 'rb'))
    if img.shape[0]/img.shape[1] < 0.5265:
        padded = True
        pad_height = int((img.shape[1] * 0.5265)/2)
        pad = np.zeros((pad_height, img.shape[1], 3), dtype=np.uint8)
        img = np.concatenate((pad, img, pad), axis=0)
        for box in list_of_boxes:
            box.ymin += pad_height
            box.ymax += pad_height
    else:
        pad_height = 0
        padded = False
    while True:
        work_img = img.copy()
        for box in list_of_boxes:
            cv2.rectangle(work_img,
                          (box.xmin, box.ymin),
                          (box.xmax, box.ymax),
                          (0, 0, 255),
                          1)
        if Draw_current is True:
            current_box.xmax = mouseX
            current_box.ymax = mouseY
            cv2.rectangle(work_img,
                          (current_box.xmin, current_box.ymin),
                          (current_box.xmax, current_box.ymax),
                          (0, 255, 0),
                          1)
        cv2.line(work_img,
                 (mouseX, mouseY),
                 (mouseX + 50, mouseY),
                 (0, 255, 255),
                 1)
        cv2.line(work_img,
                 (mouseX, mouseY),
                 (mouseX, mouseY + 50),
                 (0, 255, 255),
                 1)
        cv2.imshow('image', work_img)
        k = cv2.waitKey(1) & 0xFF
        if Clicked is True:
            Clicked = False
            Draw_current = True
            current_box = Box(mouseY,
                              mouseX,
                              mouseY,
                              mouseX)
        if Unclicked is True:
            Draw_current = False
            Unclicked = False
            current_box.xmax = mouseX
            current_box.ymax = mouseY
            list_of_boxes.append(current_box)
        if k == 101:  # If 'e' is pressed
            delete_closest(list_of_boxes, mouseX, mouseY)
        if k == 27:  # If 'Esc' is pressed
            print('Operation Canceled By User')
            exit()
        if k == 8:  # If 'Backspace' is pressed
            if fidx > 0:
                fidx -= 1
                break
        if k == 13 and Clicked is not True:  # If 'Enter' is pressed
            with open(filenames[fidx][:-4]+ftype+'.checked',
                      'wb') as file_to_dump_into:
                pickle.dump(' ', file_to_dump_into)
                print(filenames[fidx][:-4]+ftype+'.checked written')
            if padded is True:
                for box in list_of_boxes:
                    box.ymin -= pad_height
                    box.ymax -= pad_height
            with open(filenames[fidx][:-4]+ftype, 'wb') as file_to_dump_into:
                pickle.dump(list_of_boxes, file_to_dump_into)
                print(filenames[fidx][:-4]+ftype+' re-written')
            fidx += 1
            break

cv2.destroyAllWindows()
