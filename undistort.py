"""Lable the designated folder of scans."""

import cv2
import argparse
import glob
import pickle

import visutil


ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_file',
                required=True,
                help='Input file to be undistorted')
args = vars(ap.parse_args())
input_filename = args['input_file']

filenames = glob.glob(input_filename)
wide_camera_cal = pickle.load(open('wide_camera_cal.p', 'rb'))

for filename in filenames:
    print("Opening {} to convert".format(filename))
    img = cv2.imread(filename, -1)
    camera_number = int(filename[-5:-4])
    if camera_number > 0:
        img = cv2.undistort(img,
                            wide_camera_cal[0],
                            wide_camera_cal[1],
                            wide_camera_cal[2],
                            wide_camera_cal[3])
        visutil.write_image(img, filename)
