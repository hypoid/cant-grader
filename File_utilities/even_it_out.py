"""A simple script that takes a folder with 2 sub folders and evens them."""

import os
import argparse
import sys
import traceback
import pdb
import random
import glob


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info


ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_folder',
                required=True,
                help='Folder containing sub-folders')
args = vars(ap.parse_args())

input_root = args['input_folder']
if input_root[-1] is not '/':
    input_root += '/'
if not os.path.exists(input_root):
    print('Invalid input folder: {}'.format(input_root))
    exit()


sub_folders = glob.glob(input_root+'*/')

folder_pic_counts = []
smallest = len(glob.glob(sub_folders[0]+'*.jpg'))
for sub_folder in sub_folders:
    pic_count = len(glob.glob(sub_folder+'*.jpg'))
    folder_pic_counts.append(pic_count)
    print(sub_folder, pic_count)
    if pic_count < smallest:
        smallest = pic_count
print("Working...")
for index, sub_folder in enumerate(sub_folders):
    if folder_pic_counts[index] > smallest:
        probability = smallest / folder_pic_counts[index]
        pics = glob.glob(sub_folder+'*.jpg')
        for pic in pics:
            if random.random() > probability:
                os.remove(pic)

for sub_folder in sub_folders:
    pic_count = len(glob.glob(sub_folder+'*.jpg'))
    folder_pic_counts.append(pic_count)
    print(sub_folder, pic_count)

