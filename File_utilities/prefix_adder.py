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
ap.add_argument('-p', '--prefix',
                required=True,
                help='Prefix to add to files')
args = vars(ap.parse_args())
root = args['input_folder']
prefix = args['prefix']

if root[-1] is not '/':
    root += '/'
if not os.path.exists(root):
    print('Invalid root: {}'.format(root))
    exit()
all_files = os.listdir(root)

for filename in all_files:
    old = root+filename
    new = root+prefix+filename
    print('Renaming {} to {}'.format(old, new))
    os.rename(old, new)
