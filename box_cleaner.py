import pickle
import os
import glob

import argparse

ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_folder',
                required=True,
                help='Folder containing scans')
size = 300
args = vars(ap.parse_args())

input_root = args['input_folder']
if input_root[-1] is not '/':
    input_root += '/'
if not os.path.exists(input_root):
    print('Invalid input folder: {}'.format(input_root))
    exit()

filenames = glob.glob(input_root+'*.cant')
filenames += glob.glob(input_root+'*.knots')
for filename in filenames:
    print('opening {}'.format(filename))
    with open(filename, 'rb') as fid:
        boxes = pickle.load(fid)
    for box in boxes:
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
    with open(filename, 'wb') as fid:
        pickle.dump(boxes, fid)
        print('Saved {}'.format(filename))
