
import cv2
import threading
import pdb
import sys
import traceback
import argparse
import os

import visutil


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--camera number", nargs='+',
                type=int,
                required=True, help="Camera Number")
args = vars(ap.parse_args())
cam_num = args['camera number'][0]

v = ["rtsp://root:millelec01@10.0.1.10:554/axis-media/media.amp",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/101/",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/201/",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/301/",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/401/"]

stream = v[cam_num]
if cam_num == 0:
    the_cam = visutil.camera(stream, cam_num, rectify=True)
else:
    the_cam = visutil.camera(stream, cam_num, queueSize=15)
t = threading.Thread(target=visutil.poll_camera,
                     args=(the_cam,),
                     daemon=True)
t.start()
i = 1
path = "Calibration/{}.png".format(i)
while os.path.isfile(path):
    i += 1
    path = "Calibration/{}.png".format(i)

cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)

while True:
    img = the_cam.img  # Get the latest image from camera
    path = "Calibration/{}.png".format(i)
    visutil.write_image(img, path)
    print("Saving {}".format(path))
    i += 1
    cv2.imshow('image', img)
    k = cv2.waitKey(1000) & 0xFF
    if k == 27:
        print("Esc key pressed: Exiting")
        break
the_cam.destroy()
