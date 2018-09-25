import os
import glob
import shutil
import pdb
import sys
import traceback


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info

scanpaths = os.listdir('TFRecord/')
for scan in scanpaths:
    knotshere = False
    image = 'TFRecord/{}/1.png'.format(scan)
    if not os.path.isfile(image+'.knots'):
        print('Deleting {}'.format(scan))
        shutil.rmtree('TFRecord/'+scan)


