"""A script to calibrate cameras based on images in the Calibration/ dir.

Expects png image files of a 9x6 (corners) checkerboard.
"""
import numpy as np
import cv2
import glob
import sys
import pdb
import traceback
import pickle


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info
x = 9
y = 6
# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((y*x, 3), np.float32)
objp[:, :2] = np.mgrid[0:x, 0:y].T.reshape(-1, 2)

# Arrays to store object points and image points from all the images.
objpoints = []  # 3d point in real world space
imgpoints = []  # 2d points in image plane.

images = glob.glob('Calibration/*.png')

i = 0
for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, (x, y), None)

    # If found, add object points, image points (after refining them)
    if ret is True:
        i += 1
        print(i)
        print('Chessboard Corners Found in {}'.format(fname))
        objpoints.append(objp)

        corners2 = cv2.cornerSubPix(gray,
                                    corners,
                                    (11, 11),
                                    (-1, -1),
                                    criteria)
        imgpoints.append(corners2)

        # Draw and display the corners
        cv2.drawChessboardCorners(img, (x, y), corners2, ret)
        cv2.imshow('img', img)
        cv2.waitKey(1)
cv2.destroyAllWindows()
if len(imgpoints) < 10:
    print("Not enough pictures with corners detected, need at least 10")
    exit()

ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints,
                                                   imgpoints,
                                                   gray.shape[::-1],
                                                   None,
                                                   None)
h, w = img.shape[:2]
newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
wide_camera_cal = [mtx, dist, None, newcameramtx]
with open('wide_camera_cal.p', 'wb') as file_to_dump_into:
    pickle.dump(wide_camera_cal, file_to_dump_into)
    print("writing 'wide_camera_cal.p'")

dst = cv2.undistort(img, mtx, dist, None, newcameramtx)

to_show = dst
cv2.imshow('img', to_show)
cv2.waitKey(0)
