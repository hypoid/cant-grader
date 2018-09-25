"""Lable the designated folder of scans."""

import cv2
import argparse
import os
import glob
import pickle
import sys
import pdb
import traceback

from detect_cants_and_knots import knot_finder
size = 300

finder = knot_finder()
DEBUG = True


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


if DEBUG:
    sys.excepthook = info


def find_cant(img, start_left=True):
    height = img.shape[0]
    i = size/2
    cants_y_coord_and_area = []
    if start_left is True:
        start = int(size/2)
        end = height-int(size/2)
        step = 10
    else:
        start = height-int(size/2)
        end = int(size/2)
        step = -10

    for j in range(start, end, step):
        # Crop the image to the current ROI
        y1 = int(j-(size/2))
        y2 = int(j+(size/2))
        x1 = int(i-(size/2))
        x2 = int(i+(size/2))
        crop = img[y1:y2, x1:x2]
        cants, _ = finder.get_cant_and_knots(crop)
        if len(cants) > 0:
            cants_y_coord_and_area.append((j, cants[0].area))

    # Pick the y coord that has the highest area
    if len(cants_y_coord_and_area) > 0:
        biggest = cants_y_coord_and_area[0]
        for indx, coord_and_area in enumerate(cants_y_coord_and_area):
            if coord_and_area[1] > biggest[1]:
                biggest = coord_and_area
    else:  # If no cants were found, we use a default y of size/2
        return size/2
    return biggest[0]


class scan(object):
    def __init__(self, cants, knots, xy):
        self.cants = cants
        self.knots = knots
        self.xy = xy


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

if root[-1] is not '/':
    root += '/'
if not os.path.exists(root):
    print('Invalid root: {}'.format(root))
    exit()
if cam_num is not None:
    all_filenames = glob.glob(root+'*/{}.png'.format(cam_num))
    all_filenames += glob.glob(root+'*/{}.jpg'.format(cam_num))
else:
    all_filenames = glob.glob(root+'*/*.png'.format(cam_num))
    all_filenames += glob.glob(root+'*/*.jpg'.format(cam_num))

for filename in all_filenames:
    final_list_of_knots = []
    final_list_of_cants = []
    camera_number = int(filename[-5:-4])
    if cam_num is not None and cam_num != camera_number:
        continue
    print("Opening {} to annotate".format(filename))
    img = cv2.imread(filename, -1)
    width = img.shape[1]
    height = img.shape[0]
    scans = []
    y = find_cant(img, start_left=True)
    for x in range(int(size/2), width-int(size/2), 200):
        # Crop the image to the current ROI
        y1 = int(y-(size/2))
        y2 = int(y+(size/2))
        x1 = int(x-(size/2))
        x2 = int(x+(size/2))
        crop = img[y1:y2, x1:x2]
        cants, knots = finder.get_cant_and_knots(crop)
        scans.append(scan(cants, knots, (x, y)))
    for view in scans:
        x, y = view.xy
        y1 = int(y-(size/2))
        y2 = int(y+(size/2))
        x1 = int(x-(size/2))
        x2 = int(x+(size/2))
        xoffset = x1
        yoffset = y1

        list_of_knots = view.knots
        for box in list_of_knots:
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
            box.xmin = box.xmin + xoffset
            box.xmax = box.xmax + xoffset
            box.ymin = box.ymin + yoffset
            box.ymax = box.ymax + yoffset
        final_list_of_knots += list_of_knots

    with open(filename[:-4]+'.knots', 'wb') as file_to_dump_into:
        pickle.dump(final_list_of_knots, file_to_dump_into)
        print(filename[:-4]+'.knots'+' written')

cv2.destroyAllWindows()
