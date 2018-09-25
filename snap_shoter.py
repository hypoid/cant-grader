"""Select regions of interest and save them to disk."""

import cv2
import pickle
import threading
import time
import traceback
import pdb
import sys

import visutil


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info


def mouse_handler(event, x, y, flags, param):
    """Update the mouse position as mouse move events call this function."""
    global mouseX, mouseY, ROI_List
    z = 0
    if event == cv2.EVENT_LBUTTONDOWN:
        ROI_List.append([x*SCALE, y*SCALE, z])
        mouseX, mouseY = x, y
    elif event == cv2.EVENT_MOUSEMOVE:
        mouseX, mouseY = x*SCALE, y*SCALE


v = ["rtsp://root:millelec01@10.0.1.10:554/axis-media/media.amp",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/101/",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/201/",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/301/",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/401/"]

LIVE = True
SCALE = 4

if LIVE is True:
    cams = []
    first = True
    for vstream in v:
        if first:
            new_cam = visutil.camera(vstream)
            first = False
        else:
            new_cam = visutil.camera(vstream, queueSize=15)
        t = threading.Thread(target=visutil.poll_camera,
                             args=(new_cam,),
                             daemon=True)
        t.start()
        cams.append(new_cam)
else:
    first = True
    cams = []
    for vstream in v:
        if first is True:
            new_cam = visutil.big_fake_camera("Dummy")
            first = False
        else:
            new_cam = visutil.small_fake_camera("Dummy")
        t = threading.Thread(target=visutil.poll_camera,
                             args=(new_cam,),
                             daemon=True)
        t.start()
        cams.append(new_cam)

print("Waiting 5 seconds while cameras connect.")
time.sleep(5)


imgs = [cam.img for cam in cams]
all_together = visutil.combine_img_5_to_1(imgs)

size = 224
ROI_List = []
mouseX, mouseY = 100, 100
cv2.namedWindow('image')
cv2.setMouseCallback('image', mouse_handler)

# Allow the user to place the sampling boxes
while True:
    imgs = [cam.img for cam in cams]
    img = visutil.combine_img_5_to_1(imgs)

    cv2.imshow('image', img[::4, ::4, :])
    k = cv2.waitKey(1) & 0xFF
    if k == 27:
        print("Operation Canceled By User")
        exit()
    elif k == 13:
        visutil.write_image(img, "testing_snapshot.png")
cv2.destroyAllWindows()
