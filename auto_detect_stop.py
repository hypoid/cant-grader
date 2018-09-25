
import cv2
import threading
import pdb
import sys
import traceback
import time

import visutil


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


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
                                 rectify=True)
        first = False
    else:
        new_cam = visutil.camera(vstream,
                                 cam_num,
                                 queueSize=15,
                                 rectify=True,
                                 undistort=True)
    t = threading.Thread(target=visutil.poll_camera,
                         args=(new_cam,),
                         daemon=True)
    t.start()
    cams.append(new_cam)

print("Waiting 5 seconds while the cameras fully connect.")
time.sleep(5)

cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)

move_thresh = 2000
current_cam = 0
img = cams[current_cam].img  # Get the latest image from camera
last_img = img
while True:
    last_img = img
    img = cams[current_cam].img  # Get the latest image from camera
    # if cams[current_cam].moving is True:
    #     print("Moving")
    # else:
    #     print("Stopped")
    print(cams[current_cam].movement)
    cv2.imshow('image', img)
    k = cv2.waitKey(1) & 0xFF
    if k == 27:
        print("Esc key pressed: Exiting")
        break
    elif k == 81:
        current_cam -= 1
        if current_cam < 0:
            current_cam = len(cams)-1
    elif k == 83:
        current_cam += 1
        if current_cam > len(cams)-1:
            current_cam = 0
for cam in cams:
    cam.destroy()
