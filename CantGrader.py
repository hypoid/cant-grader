"""Grade when told to by the PLC."""

import cv2
import time
# import argparse
import numpy as np
import threading
import pdb
import sys
import traceback
import pickle
import tensorflow as tf
import subprocess

import visutil

LIVE = True


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info

# ap = argparse.ArgumentParser()
# ap.add_argument("-v", "--videos", nargs='+',
#                 required=True, help="Video Path")
# args = vars(ap.parse_args())
# streams = args['videos']

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
                                 rectify=True)
        first = False
    else:
        new_cam = visutil.camera(vstream,
                                 cam_num,
                                 queueSize=15,
                                 undistort=True)
    t = threading.Thread(target=visutil.poll_camera,
                         args=(new_cam,),
                         daemon=True)
    t.start()
    cams.append(new_cam)

print("Waiting 5 seconds while the cameras fully connect.")
time.sleep(5)
# Grab an initial image so we have something to show at the start
imgs = [cam.img for cam in cams]
all_together = visutil.combine_img_5_to_1(imgs)
to_show = all_together.copy()

# Define the pre-trained neural network details and load it (the "graph")
model_file = "graph.pb"
input_layer = "input"
output_layer = "final_result"
graph = visutil.load_graph(model_file)

# Define and create the tensorflow objects needed to run the neural network
input_name = "import/" + input_layer
output_name = "import/" + output_layer
input_operation = graph.get_operation_by_name(input_name)
output_operation = graph.get_operation_by_name(output_name)

ROI_list = pickle.load(open("Production_ROI_list.p", "r"))
size = 224

post_grade_delay_timer = visutil.simple_timer(3.0)
input_reader = subprocess.Popen("IO_Adapter/Input/INPUT",
                                stdout=subprocess.PIPE)

grade = "Unknown"
# All done with setup, let's grade some stuff
with tf.Session(graph=graph) as sess:
    for input_word in iter(input_reader.stdout.readline, ''):
        for cam in cams:
            if cam.ret is False:
                raise ValueError("{} offline, exiting main thread.".
                                 format(cam.path))
        if input_word == "0xFF\n" and post_grade_delay_timer.is_done():
            # 0xFF == 11111111
            # Got 'Grade NOW' signal, grading...
            post_grade_delay_timer.restart()
            imgs = [cam.img for cam in cams]
            all_together = visutil.combine_img_5_to_1(imgs)
            to_show = all_together.copy()
            grade = "Unknown"
            for point in ROI_list:
                # Pull a piece of the image for the network to evaluate
                x = point[0]
                y = point[1]
                y1 = int(y-(size/2))
                y2 = int(y+(size/2))
                x1 = int(x-(size/2))
                x2 = int(x+(size/2))
                crop = all_together[y1:y2, x1:x2]

                # Format the region so that tensorflow understands it
                numpy_frame = np.asarray(crop)
                numpy_frame = cv2.normalize(numpy_frame.astype('float'),
                                            None,
                                            -0.5,
                                            .5,
                                            cv2.NORM_MINMAX)
                t = np.expand_dims(numpy_frame, axis=0)

                # Run the region through the network to get a decision
                results = sess.run(output_operation.outputs[0],
                                   {input_operation.outputs[0]: t})
                results = np.squeeze(results)
                if results[1] > results[0]:
                    grade = "Bad"
                    # We found a bad spot, no reason to evaluate the rest
                    break
                else:
                    grade = "Good"

        cv2.imshow(grade, to_show[::4, ::4, :])
        k = cv2.waitKey(1) & 0xFF
        if k == 27:
            print("Esc key pressed: Exiting")
            exit()

        if grade != "Unknown":
            if grade == "Good":
                print("Sending 'Good' Signal..")
                subprocess.call("IO_Adapter/Output/Send_Good")
            elif grade == "Bad":
                print("Sending 'Bad' Signal..")
                subprocess.call("IO_Adapter/Output/Send_Bad")
            grade = "Unknown"

    for cam in cams:
        cam.destroy()
