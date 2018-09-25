"""Lable the designated folder of scans."""

import argparse
import os
import traceback
import pdb
import sys


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


DEBUG = True
if DEBUG:
    sys.excepthook = info
mouseX, mouseY = 100, 100

ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_folder',
                required=True,
                help='Folder containing files to rename')
args = vars(ap.parse_args())
root = args['input_folder']

if root[-1] is not '/':
    root += '/'
if not os.path.exists(root):
    print('Invalid root: {}'.format(root))
    exit()
all_files = os.listdir(root)

for filename in all_files:
    if filename.count('.') == 2:
        old = root+filename
        new = (root +
               filename[:filename.find('.')] +
               filename[filename.find('.')+1:])
        print('Renaming {} to {}'.format(old, new))
        os.rename(old, new)
