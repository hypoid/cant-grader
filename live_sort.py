"""Record blank decision frames to be converted later for training."""

import time
# import argparse
# import numpy as np
import threading
import pdb
import sys
import traceback
import subprocess
import visutil
show = False
if show is True:
    import cv2


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
if LIVE is True:
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
i = 0
print("Waiting 5 seconds while cameras connect.")
time.sleep(5)

input_reader = subprocess.Popen("IO_Adapter/Input/INPUT",
                                stdout=subprocess.PIPE)

imgs = [cam.img for cam in cams]
all_together = visutil.combine_img_5_to_1(imgs)
post_grade_delay_timer = visutil.simple_timer(3.0)

for input_word in iter(input_reader.stdout.readline, ''):
    for cam in cams:
        if cam.ret is False:
            raise ValueError("{} offline, exiting main thread.".
                             format(cam.path))
    if input_word != "0xFC\n" and post_grade_delay_timer.is_done():
        # We got an input, let's prepare to save images
        # 0xFC == 11111100 == Both grade inputs are low

        # Lock out saving another sample for 3 seconds
        post_grade_delay_timer.restart()
        imgs = [cam.img for cam in cams]
        all_together = visutil.combine_img_5_to_1(imgs)
        i += 1
        if input_word == "0xFD\n":
            # 0xFD == 11111101 == 'True' input is high
            print("Saving 'True' sample.")
            path = "Live_Sorted/true/"+str(i)+".png"
            imgs = [cam.img for cam in cams]
            visutil.write_image(all_together, path)
        elif input_word == "0xFE\n":
            # 0xFE == 11111110 == 'False' input is high
            print("Saving 'False' sample.")
            path = "Live_Sorted/false/"+str(i)+".png"
            imgs = [cam.img for cam in cams]
            visutil.write_image(all_together, path)

        if show is True:
            to_show = all_together[::4, ::4, :].copy()
            cv2.imshow('image', to_show)
            k = cv2.waitKey(1) & 0xFF
            if k == 27:
                print("Esc key pressed: Exiting")
                exit()
            elif k == 13:
                break
for cam in cams:
    cam.destroy()
