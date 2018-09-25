"""Grade when the signal is given"""

import time
# import argparse
# import numpy as np
import threading
import subprocess
import visutil
import numpy as np
import traceback
import pdb
import sys


LIVE = True
DEBUG = False
USEMOTION = False
size = 300


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


if DEBUG:
    sys.excepthook = info


def save_now(topimg, botimg):

    # Save to disk
    fold = "/data/All_training_data/Unsorted/{}/".format(
        time.time())
    visutil.write_image_set([topimg, botimg], fold)
    print("Saving scan to {}.".format(fold))


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
                                 queueSize=8,
                                 rectify=True)
        first = False
    else:
        new_cam = visutil.camera(vstream,
                                 cam_num,
                                 rectify=True,
                                 undistort=True,
                                 queueSize=21)
    t = threading.Thread(target=visutil.poll_camera,
                         args=(new_cam,),
                         daemon=True)
    t.start()
    if USEMOTION is True:
        t2 = threading.Thread(target=visutil.motion_detect,
                              args=(new_cam,),
                              daemon=True)
        t2.start()
    cams.append(new_cam)

print("Waiting 5 seconds while cameras connect.")
time.sleep(5)

input_reader = subprocess.Popen("IO_Adapter/Input/INPUT",
                                stdout=subprocess.PIPE)

imgs = [cam.img for cam in cams]
d_top_img = imgs[0]
d_bot_img = np.concatenate(tuple(imgs[1:5]), axis=1)

post_grade_delay_timer = visutil.simple_timer(preset=2.0)
save_now_delay_timer = visutil.simple_timer(preset=0.001)
grade_right_now = False

for input_word in iter(input_reader.stdout.readline, ''):
    if (
            visutil.input_means_GRADENOW(input_word) and
            post_grade_delay_timer.is_done()
       ):
        grade_right_now = True  # Latch
        save_now_delay_timer.restart()

    if grade_right_now is True and save_now_delay_timer.is_done():
        # Lock out grading another sample for 3 seconds
        post_grade_delay_timer.restart()
        grade_right_now = False  # Unlatch

        # Get images
        if USEMOTION is True:
            t_stamps_good = []
            for cam in cams:
                if time.time()-cam.still_t_stamp < 1:
                    t_stamps_good.append(True)
                else:
                    t_stamps_good.append(False)
            if all(t_stamps_good) is True:
                imgs = [cam.still for cam in cams]
        else:
            imgs = [cam.img.copy() for cam in cams]
        top_img = imgs[0]
        bot_img = np.concatenate(tuple(imgs[1:5]), axis=1)

        # Grade and send signal to PLC, then save to disk
        t = threading.Thread(target=save_now,
                             args=(top_img, bot_img),
                             daemon=True)
        t.start()

    for cam in cams:
        if cam.ret is False:
            raise ValueError("{} offline, exiting main thread.".
                             format(cam.path))


for cam in cams:
    cam.destroy()
