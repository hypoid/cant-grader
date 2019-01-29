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

v = ["rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/101/",
     "rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/201/",
     "rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/301/",
     "rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/401/",
     "rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/501/",
     "rtsp://admin:millelec01@10.0.1.11:554/Streaming/Channels/601/"]

cams = []
first = True
for cam_num, vstream in enumerate(v):
    new_cam = visutil.camera(vstream,
                             cam_num,
                             rectify=False)
    t = threading.Thread(target=visutil.poll_camera,
                         args=(new_cam,),
                         daemon=True)
    t.start()
    cams.append(new_cam)

print("Waiting 5 seconds while cameras connect.")
time.sleep(5)


imgs = [cam.img for cam in cams]
i = 0
fold = "six_cams_new_raw/"+str(i)+"/"
while os.path.exists(fold):
    i += 1
    fold = "six_cams_new_raw/"+str(i)+"/"
visutil.write_image_set(imgs, fold)
print("Saving scan to {}.".format(fold))

time.sleep(15)

for cam in cams:
    cam.destroy()

