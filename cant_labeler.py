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


def mouse_handler(event, x, y, flags, param):
    """Update the mouse position as mouse move events call this function."""
    global mouseX, mouseY, Clicked, Unclicked, MClicked, MUnclicked
    if event == cv2.EVENT_LBUTTONDOWN:
        Clicked = True
        mouseX, mouseY = x, y
    if event == cv2.EVENT_MBUTTONDOWN:
        MClicked = True
        mouseX, mouseY = x, y
    if event == cv2.EVENT_LBUTTONUP:
        Unclicked = True
        mouseX, mouseY = x, y
    if event == cv2.EVENT_MBUTTONUP:
        MUnclicked = True
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


if DEBUG:
    sys.excepthook = info

mouseX, mouseY = 100, 100
Clicked = False
MClicked = False
Draw_current = False
Draw_current_horiz = False
Unclicked = False
MUnclicked = False
current_box = Box(mouseY,
                  mouseX,
                  mouseY,
                  mouseX)
cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
cv2.setMouseCallback('image', mouse_handler)

ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_folder',
                required=True,
                help='Folder containing images')
ap.add_argument('-c', '--camera',
                required=False,
                type=int,
                help='Camera')
args = vars(ap.parse_args())
cam_num = args['camera']
root = args['input_folder']
ftype = '.cant'

if root[-1] is not '/':
    root += '/'
if not os.path.exists(root):
    print('Invalid root: {}'.format(root))
    exit()
all_filenames = glob.glob(root+'*.png')
all_filenames += glob.glob(root+'*.jpg')

# Filter out images that have already been annotated
filenames = [x for x in all_filenames if not os.path.isfile(x[:-4]+ftype)]
done_filenames = [x for x in all_filenames if os.path.isfile(x[:-4]+ftype)]

if len(done_filenames) > 0:
    print("{}% Done".format((100-(len(done_filenames)/len(all_filenames)))))
    print('{}/{}'.format(len(done_filenames), len(all_filenames)))
else:
    print("0% Done")

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
            fidx += 1
        except FileNotFoundError:
            pass
        continue
    width = img.shape[1]
    height = img.shape[0]
    # cants, knots = finder.get_cant_and_knots(img)
    # list_of_boxes = cants
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
        if Draw_current_horiz is True:
            current_box.xmax = size-1
            current_box.ymax = mouseY
            cv2.rectangle(work_img,
                          (current_box.xmin, current_box.ymin),
                          (current_box.xmax, current_box.ymax),
                          (0, 255, 0),
                          1)
        cv2.line(work_img,
                 (mouseX, mouseY),
                 (mouseX + 500, mouseY),
                 (0, 255, 255),
                 1)
        cv2.line(work_img,
                 (mouseX, mouseY),
                 (mouseX - 500, mouseY),
                 (0, 255, 255),
                 1)
        cv2.imshow('image', work_img)
        k = cv2.waitKey(1) & 0xFF
        if k == 101:  # If the 'e' key is pressed
            # E is for erase
            if len(list_of_boxes) > 0:
                delete_closest(list_of_boxes, mouseX, mouseY)
        if k == 27:  # If the 'Esc' key is pressed
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
        if k == 113:  # If the 's' key is pressed
            # Just skip this one and go to the next one
            # by breaking out of the 'while' loop
            break
        if k == 13:
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
            with open(filename[:-4]+ftype, 'wb') as file_to_dump_into:
                pickle.dump(list_of_boxes, file_to_dump_into)
                print(filename[:-4]+ftype+' written')
            fidx += 1
            break
        if Clicked is True:
            Clicked = False
            Draw_current_horiz = True
            current_box = Box(mouseY,
                              1,
                              mouseY,
                              1)
        if Unclicked is True:
            Draw_current_horiz = False
            Unclicked = False
            current_box.xmax = size-1
            current_box.ymax = mouseY
            list_of_boxes.append(current_box)

        if MClicked is True:
            MClicked = False
            Draw_current = True
            current_box = Box(mouseY,
                              mouseX,
                              mouseY,
                              mouseX)
        if MUnclicked is True:
            Draw_current = False
            MUnclicked = False
            current_box.xmax = mouseX
            current_box.ymax = mouseY
            list_of_boxes.append(current_box)
cv2.destroyAllWindows()
