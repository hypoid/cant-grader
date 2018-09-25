"""Record blank decision frames to be converted later for training."""

import time
import threading
import pdb
import sys
import traceback
import visutil
import os

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
if LIVE is True:
    first = True
    for cam_num, vstream in enumerate(v):
        if first:
            new_cam = visutil.camera(vstream,
                                     cam_num,
                                     rectify=False)
            first = False
        else:
            new_cam = visutil.camera(vstream,
                                     cam_num,
                                     queueSize=15,
                                     rectify=False,
                                     undistort=False)
        t = threading.Thread(target=visutil.poll_camera,
                             args=(new_cam,),
                             daemon=False)
        t.start()
        cams.append(new_cam)
else:
    first = True
    for vstream in v:
        if first is True:
            new_cam = visutil.big_fake_camera("Dummy")
            first = False
        else:
            new_cam = visutil.small_fake_camera("Dummy")
        t = threading.Thread(target=visutil.poll_camera,
                             args=(new_cam,),
                             daemon=False)
        t.start()
        cams.append(new_cam)
i = 0
fold = "All_training_data/Unsorted/"+str(i)+"/"
while os.path.exists(fold):
    i += 1
    fold = "All_training_data/Unsorted/"+str(i)+"/"
print("Waiting 5 seconds while cameras connect.")
time.sleep(5)


imgs = [cam.img for cam in cams]
fold = "Scans_for_testing/Raw/"+str(i)+"/"
while os.path.exists(fold):
    i += 1
    fold = "Scans_for_testing/Raw/"+str(i)+"/"
visutil.write_image_set(imgs, fold)
print("Saving scan to {}.".format(fold))

time.sleep(15)

for cam in cams:
    cam.destroy()

