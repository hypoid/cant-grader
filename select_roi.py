"""Select regions of interest and save them to disk."""

import cv2
import pickle
import threading
import time
import traceback
import pdb
import sys
import argparse
import numpy as np

import visutil


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info


def mouse_handler(event, x, y, flags, param):
    """Update the mouse position as mouse move events call this function."""
    global mouseX, mouseY, ROI_list, cam_num
    if event == cv2.EVENT_MBUTTONDOWN:
        mouseX, mouseY = x, y
        ROI_list[cam_num].append([x, y-pad_height])
    elif event == cv2.EVENT_MOUSEMOVE:
        mouseX, mouseY = x, y


v = ["rtsp://root:millelec01@10.0.1.10:554/axis-media/media.amp",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/101/",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/201/",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/301/",
     "rtsp://admin:millelec01@192.168.16.9:554/Streaming/Channels/401/"]

ap = argparse.ArgumentParser()
ap.add_argument('-p', '--Production',
                required=False,
                type=bool,
                help='Production: True if used for grading')
args = vars(ap.parse_args())
production = args['Production']

# Turn the rtsp paths into camera objects contained in a
# list called 'cams'
cams = []
first = True
for cam_num, vstream in enumerate(v):
    if first:
        new_cam = visutil.camera(vstream,
                                 cam_num,
                                 rectify=True,
                                 undistort=False)
        first = False
    else:
        new_cam = visutil.camera(vstream,
                                 cam_num,
                                 undistort=True,
                                 rectify=True,
                                 queueSize=13)
    t = threading.Thread(target=visutil.poll_camera,
                         args=(new_cam,),
                         daemon=True)
    t.start()
    cams.append(new_cam)

print("Waiting 5 seconds while cameras connect.")
time.sleep(5)


imgs = [cam.img for cam in cams]

size = 224
mouseX, mouseY = 100, 100
cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
cv2.setMouseCallback('image', mouse_handler)

if production is not True:
    try:
        ROI_list = pickle.load(open('ROI_list.p', 'rb'))
    except FileNotFoundError:
        ROI_list = [[] for cam in cams]
else:
    try:
        ROI_list = pickle.load(open('Production_ROI_list.p', 'rb'))
    except FileNotFoundError:
        ROI_list = [[] for cam in cams]

for cam_num, cam in enumerate(cams):
    while True:
        img = cam.img.copy()
        if img.shape[0]/img.shape[1] < 0.5265:
            padded = True
            pad_height = int((img.shape[1] * 0.5265)/2)
            pad = np.zeros((pad_height, img.shape[1], 3), dtype=np.uint8)
            img = np.concatenate((pad, img, pad), axis=0)
        else:
            pad_height = 0
            padded = False
        cv2.rectangle(img,
                      (mouseX-int(size/2), mouseY-int(size/2)),
                      (mouseX+int(size/2), mouseY+int(size/2)),
                      (0, 255, 255),
                      4)
        for point in ROI_list[cam_num]:
            cv2.rectangle(img,
                          (point[0]-int(size/2),
                           point[1]-int(size/2)+pad_height),
                          (point[0]+int(size/2),
                           point[1]+int(size/2)+pad_height),
                          (0, 0, 255),
                          4)
        cv2.imshow('image',
                   img)
        k = cv2.waitKey(1) & 0xFF
        if k == 101:
            if len(ROI_list[cam_num]) > 0:
                ROI_list[cam_num].pop(-1)
        elif k == 27:
            print("Esc key pressed: Exiting")
            for cam in cams:
                cam.destroy()
            cv2.destoryAllWindows()
            exit()
        elif k == 13:
            break

cv2.destroyAllWindows()

if production is True:
    with open("Production_ROI_list.p", 'wb') as ROIfile:
        pickle.dump(ROI_list, ROIfile)
        print("Saving to Production_ROI_list.p")
else:
    with open("ROI_list.p", 'wb') as ROIfile:
        pickle.dump(ROI_list, ROIfile)
        print("Saving to ROI_list.p")
