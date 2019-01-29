"""A utility to see what the cameras see."""
import cv2
import threading
import pdb
import sys
import traceback
import time
import argparse
import numpy as np

import visutil


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info

ap = argparse.ArgumentParser()
ap.add_argument('-f', '--fake',
                default=False,
                help='Use fake cameras.',
                action='store_true')
args = vars(ap.parse_args())
use_fake = args['fake']

v = ["rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/101/",
     "rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/201/",
     "rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/301/",
     "rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/401/",
     "rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/501/",
     "rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/601/"]

cams = []
first = True
for cam_num, vstream in enumerate(v):
    if cam_num < 4:
        new_cam = visutil.camera(vstream,
                                 cam_num,
                                 queueSize=13,
                                 rectify=True,
                                 undistort=True,
                                 fake=use_fake)
    else:
        new_cam = visutil.camera(vstream,
                                 cam_num,
                                 queueSize=1,
                                 rectify=True,
                                 undistort=True,
                                 fake=use_fake)
    t = threading.Thread(target=visutil.poll_camera,
                         args=(new_cam,),
                         daemon=True)
    t.start()
    cams.append(new_cam)

print("Waiting 2 seconds while the cameras fully connect.")
time.sleep(2)

cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)

imgs = [cam.img for cam in cams]
pad_height = imgs[0].shape[0]
pad_1_width = 57
pad_1 = np.zeros((pad_height, pad_1_width, 3), dtype=np.uint8)
pad_2_width = 57
pad_2 = np.zeros((pad_height, pad_2_width, 3), dtype=np.uint8)
pad_3_width = 56
pad_3 = np.zeros((pad_height, pad_3_width, 3), dtype=np.uint8)

while True:
    imgs = [cam.img for cam in cams]
    bot_img = np.concatenate((imgs[0], pad_1,
                              imgs[1], pad_2,
                              imgs[2], pad_3,
                              imgs[3]),
                             axis=1)
    top_img = np.concatenate((np.flip(imgs[4], axis=1),
                              np.flip(imgs[5], axis=1)),
                             axis=1)
    full_img = np.concatenate((top_img, bot_img), axis=0)
    cv2.imshow('image', full_img)
    k = cv2.waitKey(1) & 0xFF
    if k == 27:
        print("Esc key pressed: Exiting")
        break
for cam in cams:
    cam.destroy()
