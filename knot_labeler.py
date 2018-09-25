"""Lable the designated folder of scans."""

import cv2
import argparse
import os
import glob
import pickle
import sys
import pdb
import traceback

from detect_cants_and_knots import Box
size = 300


DEBUG = True


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


if DEBUG:
    sys.excepthook = info


def mouse_handler(event, x, y, flags, param):
    """Update the mouse position as mouse move events call this function."""
    global mouseX, mouseY, Clicked, Unclicked
    if event == cv2.EVENT_LBUTTONDOWN:
        Clicked = True
        mouseX, mouseY = x, y
    if event == cv2.EVENT_LBUTTONUP:
        Unclicked = True
        mouseX, mouseY = x, y
    elif event == cv2.EVENT_MOUSEMOVE:
        mouseX, mouseY = x, y


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
ap.add_argument('-c', '--camera',
                required=False,
                type=int,
                help='Camera')
args = vars(ap.parse_args())
cam_num = args['camera']
root = args['input_folder']
ftype = '.knots'

if root[-1] is not '/':
    root += '/'
if not os.path.exists(root):
    print('Invalid root: {}'.format(root))
    exit()
if cam_num is not None:
    all_filenames = glob.glob(root+'*/{}.jpg'.format(cam_num))
else:
    all_filenames = glob.glob(root+'*/*.jpg'.format(cam_num))
if len(glob.glob(root+'*.jpg')) > len(all_filenames):
    all_filenames = glob.glob(root+'*.jpg')

# Filter out images that have already been annotated
filenames = [x for x in all_filenames if not os.path.isfile(x[:-4]+ftype)]
done_filenames = [x for x in all_filenames if os.path.isfile(x[:-4]+ftype)]

num_done = len(done_filenames)
if num_done > 0:
    print("{}% Done".format(num_done/len(all_filenames)))
else:
    print('0% Done')

# For each scan's file, allow the user to place bounding boxes
fidx = 0
while fidx < len(filenames) and fidx > -1:
    filename = filenames[fidx]
    final_list_of_boxes = []
    camera_number = int(filename[-5:-4])
    if cam_num is not None and cam_num != camera_number:
        continue
    print("Opening {} to annotate".format(filename))
    img = cv2.imread(filename, -1)
    if img is None:
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
        fidx += 1
        continue
    width = img.shape[1]
    height = img.shape[0]
    list_of_boxes = []
    while True:
        work_img = img.copy()
        for box in list_of_boxes:
            cv2.rectangle(work_img,
                          (box.xmin, box.ymin),
                          (box.xmax, box.ymax),
                          (0, 255, 255),
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
        if k == 101:
            if len(list_of_boxes) > 0:
                list_of_boxes.pop(-1)
        if k == 27:
            print('Operation Canceled By User')
            exit()
        if k == 112:  # If the 'p' key is pressed
            # P is for purge
            os.remove(filename)
            print("Deleted {}".format(filename))
            fidx += 1
            filenames.pop(fidx)
        if k == 8:  # If 'Backspace' is pressed
            if fidx > 0:
                fidx -= 1
                break
        elif k == 13:
            for box in list_of_boxes:
                if box.ymax < box.ymin:
                    true_min = box.ymax
                    true_max = box.ymin
                    box.ymin = true_min
                    box.ymax = true_max
                if box.xmax < box.xmin:
                    true_min = box.xmax
                    true_max = box.xmin
                    box.xmin = true_min
                    box.xmax = true_max
                if box.xmin > size-1:
                    box.xmin = size-1
                if box.xmax > size-1:
                    box.xmax = size-1
                if box.ymin > size-1:
                    box.ymin = size-1
                if box.ymax > size-1:
                    box.ymax = size-1
                if box.xmin < 1:
                    box.xmin = 1
                if box.xmax < 1:
                    box.xmax = 1
                if box.ymin < 1:
                    box.ymin = 1
                if box.ymax < 1:
                    box.ymax = 1
            final_list_of_boxes += list_of_boxes
            list_of_boxes = []
            fidx += 1
            break
        if Clicked is True:
            Clicked = False
            Draw_current = True
            current_box = Box(mouseY,
                              mouseX,
                              mouseY,
                              mouseX,
                              1)
        if Unclicked is True:
            Draw_current = False
            Unclicked = False
            current_box.xmax = mouseX
            current_box.ymax = mouseY
            list_of_boxes.append(current_box)
    with open(filename[:-4]+ftype, 'wb') as file_to_dump_into:
        pickle.dump(final_list_of_boxes, file_to_dump_into)
        print(filename[:-4]+ftype+' written')
cv2.destroyAllWindows()
