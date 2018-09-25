"""Convert all png images to jpg in the current dir."""
import glob
import os
import cv2
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_folder',
                required=True,
                help='Folder containing scans')
args = vars(ap.parse_args())
input_dir = args['input_folder']
if input_dir[-1] is not '/':
    input_dir += '/'
if not os.path.exists(input_dir):
    print('Invalid input folder: {}'.format(input_dir))
    exit()

for filename in glob.glob(input_dir+'*.png'):
    a = cv2.imread(filename)
    if False:
        cv2.imwrite(filename[:-4]+'.png', a, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        print('Reading {}, writing {}.png'.format(filename, filename[:-4]))
    else:
        cv2.imwrite(filename[:-4]+'.jpg', a, [cv2.IMWRITE_JPEG_QUALITY, 90])
        print('Reading {}, writing {}.jpg'.format(filename, filename[:-4]))
