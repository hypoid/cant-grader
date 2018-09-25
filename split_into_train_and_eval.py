"""A simple script that takes a folder with 2 sub folders and evens them."""

import os
import argparse
import sys
import traceback
import pdb
import random
import glob
import shutil


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info


ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_folder',
                required=True,
                help='Folder containing sub-folders')
ap.add_argument('-t', '--train_percent',
                required=True,
                type=int,
                help='Train percentage')
args = vars(ap.parse_args())

train_percentage = args['train_percent']
input_root = args['input_folder']

if input_root[-1] is not '/':
    input_root += '/'
if not os.path.exists(input_root):
    print('Invalid input folder: {}'.format(input_root))
    exit()

try:
    shutil.rmtree(input_root+'eval/')
    shutil.rmtree(input_root+'train/')
    os.mkdir(input_root+'eval/')
    os.mkdir(input_root+'train/')
except:
    os.mkdir(input_root+'eval/')
    os.mkdir(input_root+'train/')

sub_folders = glob.glob(input_root+'*/')

probability = train_percentage / 100
if probability > 1:
    print('Invalid percentage {}%'.format(train_percentage))
    exit()
i = 0
for sub_folder in sub_folders:
    i += 1
    if random.random() > probability:
        newpath = '{}eval/{}'.format(input_root,i)
        print('Moving {} to {}'.format(sub_folder, newpath))
        shutil.copytree(sub_folder, newpath)
    else:
        newpath = '{}train/{}'.format(input_root,i)
        print('Moving {} to {}'.format(sub_folder, newpath))
        shutil.copytree(sub_folder, newpath)
