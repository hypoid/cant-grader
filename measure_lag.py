"""Record scans to be converted later for training."""

import time
# import argparse
# import numpy as np
import threading
import pdb
import sys
import traceback
import visutil
import cv2

LIVE = True
DEBUG = False


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


if DEBUG is True:
    sys.excepthook = info

v = ["rtsp://root:millelec01@10.0.1.10:554/axis-media/media.amp",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/101/",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/201/",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/301/",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/401/"]

cams = []
first = True
for cam_num, vstream in enumerate(v):
    if first:
        new_cam = visutil.camera(vstream,
                                 cam_num,
                                 queueSize=1,
                                 rectify=True)
        first = False
    else:
        new_cam = visutil.camera(vstream,
                                 cam_num,
                                 rectify=True,
                                 undistort=True,
                                 queueSize=10)
    t = threading.Thread(target=visutil.poll_camera,
                         args=(new_cam,),
                         daemon=True)
    t.start()
    t2 = threading.Thread(target=visutil.motion_detect,
                          args=(new_cam,),
                          daemon=True)
    t2.start()
    cams.append(new_cam)

print("Waiting 5 seconds while cameras connect.")
time.sleep(1)

for cam_num in range(len(cams)):
    cv2.namedWindow(str(cam_num), flags=cv2.WINDOW_NORMAL)

timing = False
start_time = time.time()
finnish_line = [True for cam in cams]
was = [False for cam in cams]
while True:
    for cam in cams:
        if cam.ret is False:
            raise ValueError("{} offline, exiting main thread.".
                             format(cam.path))
    # print([cam.movement for cam in cams])
    moving_flags = [cam.moving for cam in cams]
    if timing is False:
        for i, flag in enumerate(moving_flags):
            if flag is False and was[i] is True:
                print(was)
                print("starting timer")
                timing = True
                start_time = time.time()
    else:
        for i, flag in enumerate(moving_flags):
            if not moving_flags[i] and was[i]:
                print(was)
                print(time.time()-start_time)
                timing = False
        if time.time()-start_time > 3:
            print("False start, ending timer.")
            timing = False
    for i, flag in enumerate(moving_flags):
        if flag is True:
            was[i] = True
        else:
            was[i] = False
    for cam_num, cam in enumerate(cams):
        cv2.imshow(str(cam_num), cam.img)
    k = cv2.waitKey(1) & 0xFF
    if k == 27:
        print('Operation Canceled By User')
        exit()


for cam in cams:
    cam.destroy()
