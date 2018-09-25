"""Convert old boxes to new boxes."""
import os
import glob
import visutil
import cv2
import argparse
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_folder',
                required=True,
                help='Folder containing scans')
size = 300
args = vars(ap.parse_args())
list_of_flipped = []
with open('list_of_flipped', 'rb') as fid:
    for line in fid.readlines():
        list_of_flipped.append(line[8:-1].decode('UTF8'))

input_root = args['input_folder']
if input_root[-1] is not '/':
    input_root += '/'
if not os.path.exists(input_root):
    print('Invalid input folder: {}'.format(input_root))
    exit()

filenames = glob.glob(input_root+'*/0.png')
filenames += glob.glob(input_root+'*/raw/0.png')

for filename in filenames:
    if filename in list_of_flipped:
        print("Skipping previously flipped {}".format(filename))
    else:
        print("Opening {}".format(filename))
        img = cv2.imread(filename, -1)
        if img is not None:
            img = np.fliplr(img)
            cv2.imwrite(filename,
                        img,
                        [cv2.IMWRITE_PNG_COMPRESSION, 10])
            print("Wrote {}".format(filename))
        else:
            os.remove(filename)
