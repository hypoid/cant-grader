
"""Select points to define the rectification quad for each camera.


Creates/Updates a file called 'new_rectify_windows.p'
"""

import cv2
import pickle
import traceback
import pdb
import sys
import numpy as np
import threading
import time
import configparser

import visutil


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info


def draw_crosshair(img, point):
    X = int(point[0])
    Y = int(point[1])
    cv2.line(img,
             (X-10, Y),
             (X+10, Y),
             (0, 255, 255),
             1)
    cv2.line(img,
             (X, Y-10),
             (X, Y+10),
             (0, 255, 255),
             1)


def mouse_handler(event, x, y, flags, param):
    """Update the mouse position as mouse move events call this function."""
    global mouseX
    global mouseY
    global points_clicked_status
    global window_point_list
    if event == cv2.EVENT_MBUTTONDOWN:
        mouseX, mouseY = x, y
        for index, point in enumerate(window_point_list[cam_num]):
            dist = (point[0]-x)*(point[0]-x)+(point[1]-y)*(point[1]-y)
            if dist < 400:
                points_clicked_status[cam_num][index] = True
    elif event == cv2.EVENT_MBUTTONUP:
        mouseX, mouseY = x, y
        points_clicked_status[cam_num] = [False, False, False, False]
    elif event == cv2.EVENT_MOUSEMOVE:
        mouseX, mouseY = x, y
        for index, point in enumerate(window_point_list[cam_num]):
            if points_clicked_status[cam_num][index] is True:
                window_point_list[cam_num][index] = [x, y]


# except FileNotFoundError:
#     window_point_list = np.float32([[[0, 0],
#                                      [100, 0],
#                                      [100, 100],
#                                      [0, 100]],
#                                     [[0, 0],
#                                      [100, 0],
#                                      [100, 100],
#                                      [0, 100]],
#                                     [[0, 0],
#                                      [100, 0],
#                                      [100, 100],
#                                      [0, 100]],
#                                     [[0, 0],
#                                      [100, 0],
#                                      [100, 100],
#                                      [0, 100]],
#                                     [[0, 0],
#                                      [100, 0],
#                                      [100, 100],
#                                      [0, 100]],
#                                     [[0, 0],
#                                      [100, 0],
#                                      [100, 100],
#                                      [0, 100]]])

# old_list = pickle.load(open('new_rectify_windows.p', 'rb'))
window_point_list = pickle.load(open('new_rectify_windows.p', 'rb'))
# except FileNotFoundError:
#     print('ERROR: Rectification Points Not Found')
#     window_point_list = np.float32([[[0, 0],
#                                      [100, 0],
#                                      [100, 100],
#                                      [0, 100]],
#                                     [[0, 0],
#                                      [100, 0],
#                                      [100, 100],
#                                      [0, 100]],
#                                     [[0, 0],
#                                      [100, 0],
#                                      [100, 100],
#                                      [0, 100]],
#                                     [[0, 0],
#                                      [100, 0],
#                                      [100, 100],
#                                      [0, 100]],
#                                     [[0, 0],
#                                      [100, 0],
#                                      [100, 100],
#                                      [0, 100]],
#                                     [[0, 0],
#                                      [100, 0],
#                                      [100, 100],
#                                      [0, 100]]])
# 

# correct_points = np.float32([[[0, 0],
#                               [1530, 0],
#                               [1530, 460],
#                               [0, 460]],
#                              [[0, 0],
#                               [830, 0],
#                               [830, 460],
#                               [0, 460]],
#                              [[0, 0],
#                               [910, 0],
#                               [910, 460],
#                               [0, 460]],
#                              [[0, 0],
#                               [560, 0],
#                               [560, 460],
#                               [0, 460]],
#                              [[0, 0],
#                               [2000, 0],
#                               [2000, 460],
#                               [0, 460]],
#                              [[0, 0],
#                               [1980, 0],
#                               [1980, 460],
#                               [0, 460]]])

correct_points = np.float32([[[0, 0],
                              [0, 0],
                              [0, 0],
                              [0, 0]],
                             [[0, 0],
                              [0, 0],
                              [0, 0],
                              [0, 0]],
                             [[0, 0],
                              [0, 0],
                              [0, 0],
                              [0, 0]],
                             [[0, 0],
                              [0, 0],
                              [0, 0],
                              [0, 0]],
                             [[0, 0],
                              [0, 0],
                              [0, 0],
                              [0, 0]],
                             [[0, 0],
                              [0, 0],
                              [0, 0],
                              [0, 0]]])

config = configparser.ConfigParser()
config.read('cameras.config')
for cam_num, cp in enumerate(correct_points):
    cam_config = config[str(cam_num)]
    heightpx = int(
        float(cam_config['DPI']) *
        float(cam_config['ScanRegionInchesY']))
    widthpx = int(
        float(cam_config['DPI']) *
        float(cam_config['ScanRegionInchesX']))

    correct_points[cam_num] = np.float32([[0, 0],
                                          [widthpx, 0],
                                          [widthpx, heightpx],
                                          [0, heightpx]])

points_clicked_status = [[False, False, False, False],
                         [False, False, False, False],
                         [False, False, False, False],
                         [False, False, False, False],
                         [False, False, False, False],
                         [False, False, False, False]]
cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
cv2.setMouseCallback('image', mouse_handler)
mouseX = 100
mouseY = 100
Clicked = False
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
                             queueSize=15,
                             undistort=True,
                             rectify=False,
                             fake=False)
    t = threading.Thread(target=visutil.poll_camera,
                         args=(new_cam,),
                         daemon=True)
    t.start()
    cams.append(new_cam)

print("Waiting 5 seconds while the cameras fully connect.")
time.sleep(5)
for cam_num in range(len(cams)):
    print("Setting camera {}'s window".format(cam_num))
    while True:
        work_img = cams[cam_num].img.copy()
        for point in window_point_list[cam_num]:
            if point[1] > work_img.shape[0]:
                point[1] = work_img.shape[0]
            if point[0] > work_img.shape[1]:
                point[0] = work_img.shape[1]
            draw_crosshair(work_img, (point[0], point[1]))
            # cv2.circle(work_img,
            #            (point[0], point[1]),
            #            10,
            #            (50, 50, 255),
            #            -1)
        cv2.imshow('image',
                   work_img)
        k = cv2.waitKey(1) & 0xFF
        if k == 27:
            print("Operation Canceled By User")
            exit()
        elif k == 13:
            wpoints = window_point_list[cam_num]
            cpoints = correct_points[cam_num]
            m = cv2.getPerspectiveTransform(wpoints,
                                            cpoints)
            corrected_image = cv2.warpPerspective(cams[cam_num].img,
                                                  m,
                                                  (cpoints[2][0],
                                                   cpoints[2][1]))
            cv2.imshow('image', corrected_image)
            k = cv2.waitKey(0) & 0xff
            if k == 27:
                print('Redoing window..')
            elif k == 13:
                break


cv2.destroyAllWindows()
output_filename = 'new_rectify_windows.p'
with open(output_filename, 'wb') as ROIfile:
    pickle.dump(window_point_list, ROIfile)
    print("{} Written.".format(output_filename))
for cam in cams:
    cam.destroy()
