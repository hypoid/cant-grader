"""Take crops from the designated folder of scans and save them."""

import cv2
import argparse
import os
import glob
import traceback
import pdb
import sys
import pickle

import visutil


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


def mouse_handler(event, x, y, flags, param):
    """Update the mouse position as mouse move events call this function."""
    global mouseX, mouseY
    if event == cv2.EVENT_MOUSEMOVE:
        mouseX, mouseY = x, y


DEBUG = True
if DEBUG:
    sys.excepthook = info
mouseX, mouseY = 100, 100

cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
cv2.setMouseCallback('image', mouse_handler)


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

if input_root[-1] is not '/':
    input_root += '/'
if output_root[-1] is not '/':
    output_root += '/'
if not os.path.exists(input_root):
    print('Invalid input folder: {}'.format(input_root))
    exit()
if not os.path.exists(output_root):
    os.mkdir(output_root)

# Filter out images that have already been checked

size = 300
image_num = 0
while os.path.isfile(output_root+str(image_num).zfill(6)+'.tif'):
    image_num += 1
scan_folders = glob.glob(input_root+'*/')
for folder in scan_folders:
    images = glob.glob(folder+'*.tif')
    images = [x for x in images if not os.path.isfile(x+'.checked')]
    for image_name in images:
        print("Opening {} to check".format(image_name))
        orig_img = cv2.imread(image_name, -1)
        raw_img = cv2.imread(folder+'raw/'+image_name[-5:])
        while True:
            img = orig_img.copy()
            if mouseX < int(size/2)+1:
                mouseX = int(size/2)+1
            if mouseY < int(size/2)+1:
                mouseY = int(size/2)+1
            if mouseY > img.shape[0] - int(size/2)-1:
                mouseY = img.shape[0] - int(size/2)-1
            if mouseX > img.shape[1] - int(size/2)-1:
                mouseX = img.shape[1] - int(size/2)-1

            cv2.rectangle(img,
                          (mouseX-int(size/2), mouseY-int(size/2)),
                          (mouseX+int(size/2), mouseY+int(size/2)),
                          (0, 255, 255),
                          4)
            cv2.imshow('image', img)
            k = cv2.waitKey(1) & 0xFF
            if k == 32:  # If the 's' key is pressed
                y1 = int(mouseY-(size/2))
                y2 = int(mouseY+(size/2))
                x1 = int(mouseX-(size/2))
                x2 = int(mouseX+(size/2))
                crop = raw_img[y1:y2, x1:x2]
                path = output_root+str(image_num).zfill(6)+'.jpg'
                print('Saving {}'.format(path))
                visutil.write_image(crop, path)
                cv2.rectangle(orig_img,
                              (mouseX-int(size/2), mouseY-int(size/2)),
                              (mouseX+int(size/2), mouseY+int(size/2)),
                              (255, 255, 255),
                              4)
                image_num += 1
            if k == 13:  # If 'Enter' is pressed
                with open(image_name+'.checked',
                          'wb') as file_to_dump_into:
                    pickle.dump(' ', file_to_dump_into)
                    print(image_name+'.checked written')
                break
            if k == 27:  # If 'Esc' is pressed
                print('Operation Canceled By User')
                exit()

cv2.destroyAllWindows()
