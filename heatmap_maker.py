"""Generate a heatmap of activations for an image."""

import cv2
import argparse
import os
import sys
import traceback
import pdb

import visutil


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info

size = 224

ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_image',
                required=True,
                help='image to generate a heatmap from')
ap.add_argument('-o', '--output_image',
                required=True,
                help='image to export as a heatmap')
args = vars(ap.parse_args())

input_image_filename = args['input_image']
output_image_filename = args['output_image']

if not os.path.isfile(input_image_filename):
    print("{} doesn't exist".format(input_image_filename))
    exit()

print('Processing {}'.format(input_image_filename))

# Load the image from disk
img = cv2.imread(input_image_filename, -1)
work_img = img.copy()

# Generate a list of points for every point in the input image
# except those that are too close to the boarders to allow a full
# size subregion to be gotten
width = img.shape[1]
height = img.shape[0]
image_classifier = visutil.classifier('graph.pb')
for i in range(int(size/2), width-int(size/2), 1):
    for j in range(int(size/2), height-int(size/2), 1):
        print(i,j)
        # Crop the image to the current ROI
        y1 = int(j-(size/2))
        y2 = int(j+(size/2))
        x1 = int(i-(size/2))
        x2 = int(i+(size/2))
        crop = img[y1:y2, x1:x2]
        results = image_classifier.classify(crop)
        shade = int(results[0]*255)
        work_img[j][i][0] = shade

visutil.write_image(work_img, output_image_filename)
