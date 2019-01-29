import cv2
import argparse
import os
import glob
import pickle
import numpy as np

import visutil


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
filenames = glob.glob(root+'*/*.png')

windows = pickle.load(open('rectify_windows.p',
                           'rb'))
cps = np.float32([[[0, 0],
                   [5120, 0],
                   [5120, 448],
                   [0, 448]],
                  [[0, 0],
                   [1280, 0],
                   [1280, 360],
                   [0, 360]],
                  [[0, 0],
                   [1280, 0],
                   [1280, 360],
                   [0, 360]],
                  [[0, 0],
                   [1280, 0],
                   [1280, 360],
                   [0, 360]],
                  [[0, 0],
                   [1280, 0],
                   [1280, 360],
                   [0, 360]]])

for filename in filenames:
    print("Opening {} to convert".format(filename))
    img = cv2.imread(filename, -1)
    camera_number = int(filename[-5:-4])

    cp = cps[camera_number]
    window = windows[camera_number]
    M = cv2.getPerspectiveTransform(window,
                                    cp)

    img = cv2.warpPerspective(img,
                              M,
                              (cp[2][0],
                               cp[2][1]))
    visutil.write_image(img, filename)
    print("Writing {}".format(filename))
