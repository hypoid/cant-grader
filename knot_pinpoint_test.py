"""A simple script to test a model file on a hardcoded example."""
import cv2
import pdb
import sys
import traceback
import threading
import argparse

import visutil


def mouse_handler(event, x, y, flags, param):
    """Update the mouse position as mouse move events call this function."""
    global mouseX, mouseY, SCALE
    if event == cv2.EVENT_MOUSEMOVE:
        mouseX, mouseY = x*SCALE, y*SCALE


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


ap = argparse.ArgumentParser()
ap.add_argument('-f', '--fake',
                default=False,
                help='Use fake cameras.',
                action='store_true')
args = vars(ap.parse_args())
use_fake = args['fake']

sys.excepthook = info

SCALE = 1
mouseY = 300
mouseX = 300
size = 128


# Define the pre-trained neural network details and load it (the "graph")
image_classifier = visutil.classifier("knot_pinpoint.pb")

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
                                 rectify=True,
                                 fake=use_fake)
        first = False
    else:
        new_cam = visutil.camera(vstream,
                                 cam_num,
                                 queueSize=10,
                                 rectify=True,
                                 undistort=True,
                                 fake=use_fake)
    t = threading.Thread(target=visutil.poll_camera,
                         args=(new_cam,),
                         daemon=True)
    t.start()
    cams.append(new_cam)

cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
cv2.setMouseCallback('image', mouse_handler)

current_cam = 1
while True:
    img = cams[current_cam].img  # Get the latest image from camera

    frame = img.copy()
    y = int(mouseY)
    x = int(mouseX)
    if x < size/2:
        x = size/2
    if y < size/2:
        y = size/2
    if x > frame.shape[1] - size/2:
        x = frame.shape[1] - size/2
    if y > frame.shape[0] - size/2:
        y = frame.shape[0] - size/2
    y1 = int(y-(size/2))
    y2 = int(y+(size/2))
    x1 = int(x-(size/2))
    x2 = int(x+(size/2))
    crop = frame[y1:y2, x1:x2]

    results = image_classifier.classify(crop)

    if results[0] > results[1]:
        print('Bad')
    else:
        print('Good')

    shade1 = int(results[0]*255)
    shade2 = int(results[1]*255)
    cv2.rectangle(frame,
                  (int(x-(size/2)), int(y-(size/2))),
                  (int(x+(size/2)), int(y+(size/2))),
                  (0, shade2, shade1),
                  4)

    cv2.imshow('image', frame[::SCALE, ::SCALE, :])
    k = cv2.waitKey(2) & 0xFF
    if k == 27:
        cv2.destroyAllWindows()
        exit()
    elif k == 81:
        current_cam -= 1
        if current_cam < 0:
            current_cam = len(cams)-1
    elif k == 83:
        current_cam += 1
        if current_cam > len(cams)-1:
            current_cam = 0
