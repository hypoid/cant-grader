"""A library full of helper functions for the CantGrader project."""

import cv2
import numpy as np
import tensorflow as tf
import time
from collections import deque
import threading
import os
import pickle
import configparser
import math

font = cv2.FONT_HERSHEY_SIMPLEX


class classifier(object):
    """A simple classifier object to use."""

    def __init__(self, model_filename):
        """Initialize."""
        self.graph = load_graph(model_filename)
        input_layer = 'input'
        output_layer = "final_result"
        input_name = "import/" + input_layer
        output_name = "import/" + output_layer
        self.input_operation = self.graph.get_operation_by_name(input_name)
        self.output_operation = self.graph.get_operation_by_name(output_name)

    def classify(self, img):
        """Classify the given immage.

        Returns a list of probablilities: False, then True
        """
        with tf.Session(graph=self.graph) as sess:
            numpy_frame = np.asarray(img)
            numpy_frame = cv2.normalize(numpy_frame.astype('float'),
                                        None,
                                        -0.5,
                                        .5,
                                        cv2.NORM_MINMAX)
            t = np.expand_dims(numpy_frame, axis=0)

            # Run the region through the network to get a decision
            results = sess.run(self.output_operation.outputs[0],
                               {self.input_operation.outputs[0]: t})
            results = np.squeeze(results)
            return results


class bounding_box(object):
    """A simple bounding box.

    bounding_boxes have the following attributes:
        int x1 = the topleft corner x position
        int y1 = the topleft corner y position
        int x2 = the bottomright corner x position
        int y2 = the bottomright corner position
    """

    def __init__(self, x1, y1, x2, y2):
        """initialize."""
        self.x1 = int(x1)
        self.y1 = int(y1)
        self.x2 = int(x2)
        self.y2 = int(y2)

    def __repr__(self):
        """Show yourself."""
        return "bounding_box({}, {}, {}, {})".format(self.x1,
                                                     self.y1,
                                                     self.x2,
                                                     self.y2)


class simple_timer(object):
    """A simple timer that inplements various common timer functions."""

    def __init__(self, preset):
        """Initialize."""
        self.preset = preset
        self.start_time = time.time()
        self.used_time = 0.0
        self.paused = False

    def is_done(self):
        """Return True if the timer has finished its alotted time."""
        if (
            self.start_time + self.preset < time.time() and
            self.paused is False
           ):
            return True
        else:
            return False

    def restart(self):
        """Reset the timer so that it starts from 0."""
        self.start_time = time.time()
        self.paused = False
        self.used_time = 0.0

    def pause(self):
        """Pause the timer so that it doesn't time out."""
        if self.is_done() is False:
            self.used_time = time.time() - self.start_time
            self.paused = True

    def resume(self):
        """Resume the timer so that it can continue timming."""
        self.start_time = time.time() - self.used_time
        self.paused = False


class camera(object):
    """A camera that is to be polled for new images.

    Cameras have following properties:

    Attributes:
        cap: An opencv capture object that is bound to the rtsp
             stream.
        ret: The flag of the last image returned by cap.
             True means valid.
        img: The latest image from the camera.
        path: path to video used for identification.
        queueSize: How many frames to buffer before giving
                   the latest one.
        rectify: Whether to rectify the image using a
                 saved config file 'main_cam_window.p'
        fake: What it sounds like
        jit: Whether to do just in time undistort/rectification

    """

    def __init__(self,
                 rtsp_path,
                 cam_num, queueSize=2,
                 rectify=False,
                 undistort=False,
                 fake=False,
                 jit=False):
        """Connect the the camera at the specified rtsp path.

        rtsp_path: a url showing what stream to use.
                   Includes credentials, ip, etc..
        """
        self.fake = fake
        self.rectify = rectify
        self.undistort = undistort
        self.jit = jit
        if self.fake is False:
            self.cap = cv2.VideoCapture(rtsp_path)
            self.ret, self.img = self.cap.read()
            self.orig_img = self.img
        else:
            test_filename = 'camera_5&6_rect/trail/{}.png'.format(
                cam_num)
            try:
                self.orig_img = cv2.imread(test_filename)
                self.img = self.orig_img
                self.ret = True
            except FileNotFoundError:
                self.ret = False
                print("Can't load test file:{}".format(test_filename))
                exit()
        if self.ret is False:
            print("Cannot connect to {}".format(rtsp_path))
            exit()
        if self.undistort is True:
            if cam_num < 4:
                self.wide_camera_cal = pickle.load(
                    open('wide_camera_cal.p', 'rb'))
                self.img = cv2.undistort(self.img,
                                         self.wide_camera_cal[0],
                                         self.wide_camera_cal[1],
                                         self.wide_camera_cal[2],
                                         self.wide_camera_cal[3])
            else:
                self.wide_camera_cal = pickle.load(
                    open('camera_5_cal.p', 'rb'))
                self.img = cv2.undistort(self.img,
                                         self.wide_camera_cal[0],
                                         self.wide_camera_cal[1],
                                         self.wide_camera_cal[2],
                                         self.wide_camera_cal[3])
        if self.rectify is True:
            window = pickle.load(open('new_rectify_windows.p',
                                      'rb'))[cam_num]
            config = configparser.ConfigParser()
            if os.path.isfile('cameras.config') is False:
                print("Cannot find 'cameras.config', exiting.")
                exit()
            config.read('cameras.config')
            cam_config = config[str(cam_num)]
            self.heightpx = int(
                float(cam_config['DPI']) *
                float(cam_config['ScanRegionInchesY']))
            self.widthpx = int(
                float(cam_config['DPI']) *
                float(cam_config['ScanRegionInchesX']))

            self.cp = np.float32([[0, 0],
                                  [self.widthpx, 0],
                                  [self.widthpx, self.heightpx],
                                  [0, self.heightpx]])

            self.M = cv2.getPerspectiveTransform(window,
                                                 self.cp)

            self.img = cv2.warpPerspective(self.img,
                                           self.M,
                                           (self.cp[2][0],
                                            self.cp[2][1]))
        self.path = rtsp_path
        frms = []
        for i in range(queueSize):
            frms.append(self.img)
        self.frames = deque(frms)
        self.max_buff_size = queueSize
        self.moving = False
        self.still = self.img
        self.movement = 0
        if cam_num == 0:
            self.move_thresh = 2000
        else:
            self.move_thresh = 1000
        self.still_t_stamp = time.time()

    def update(self):
        """Get a new image from the camera. Return False if not valid."""
        if self.fake is False:
            self.ret, new_img = self.cap.read()
        else:
            new_img = self.orig_img
        if self.jit is False:
            if self.undistort is True:
                new_img = cv2.undistort(new_img,
                                        self.wide_camera_cal[0],
                                        self.wide_camera_cal[1],
                                        self.wide_camera_cal[2],
                                        self.wide_camera_cal[3])
            if self.rectify is True:
                new_img = cv2.warpPerspective(new_img,
                                              self.M,
                                              (self.cp[2][0],
                                               self.cp[2][1]))
            self.frames.append(new_img)
            if len(self.frames) > self.max_buff_size:
                self.frames.popleft()
            self.img = self.frames[0]
            return self.ret
        elif self.jit is True:
            self.frames.append(new_img)
            if len(self.frames) > self.max_buff_size:
                self.frames.popleft()
            self.img = self.frames[0]
            return self.ret
            

    def motion_update(self):
        """Update the motion detection attributes."""
        self.movement = compute_diff_measure(self.frames[0], self.frames[1])
        if self.movement > self.move_thresh:
            self.moving = True
        else:
            self.moving = False
            self.still_t_stamp = time.time()
            self.still = self.img

    def destroy(self):
        """Shut it down."""
        if self.destroy is False:
            self.cap.release()
        return


class display(object):
    """A display that displays new images.

    Displays have following properties:

    Attributes:
        img: The latest image given to the display.
        queueSize: How many frames to buffer for history.

    """

    def __init__(self,
                 queueSize=20,
                 resolution=(3980, 920)):
        """Setup the display with a blank history."""

        self.img = np.zeros((resolution[1], resolution[0], 3),
                            dtype=np.uint8)
        frms = []
        for i in range(queueSize):
            frms.append(self.img)
        self.frames = deque(frms)
        self.max_buff_size = queueSize

    def refresh_display_forever(self):
        """Display the current image."""
        cv2.namedWindow('Current Scan', flags=cv2.WINDOW_NORMAL)
        while True:
            #imS = cv2.resize(self.img, (math.floor(self.img.shape[1]/4), math.floor(self.img.shape[0]/4)))
            imS = self.img
            cv2.imshow('Current Scan', imS)
            k = cv2.waitKey(20) & 0xFF
            if k == 27:  # If 'Esc' is pressed
                print('Operation Canceled By User')
                exit()

    def update_display(self, new_img):
        self.frames.append(new_img)
        if len(self.frames) > self.max_buff_size:
            self.frames.popleft()
        self.img = self.frames[-1]


class small_fake_camera(object):
    """A fake camera that is to be polled for new images.

    Cameras have following properties:

    Attributes:
        cap: An opencv capture object that is bound to the rtsp
             stream.
        ret: The flag of the last image returned by cap.
             True means valid.
        img: The latest image from the camera.
        path: path to video used for identification.

    """

    def __init__(self, ID):
        """Connect the the camera at the specified rtsp path."""
        self.x = 640
        self.y = 480
        self.ID = ID
        # self.img = np.zeros((self.y, self.x, 3),
        #                     dtype=np.uint8)
        self.img.fill(255)
        self.ret = True
        self.path = "Fake"
        self.loaded_img = cv2.imread('Testing_scan/2.png', -1)
        self.img = self.loaded_img

    def update(self):
        """Get a new FAKE image from the FAKE camera."""
        self.img = self.loaded_img
        return self.ret

    def destroy(self):
        """Shut it down."""
        return


class big_fake_camera(object):
    """A fake camera that is to be polled for new images.

    Cameras have following properties:

    Attributes:
        cap: An opencv capture object that is bound to the rtsp stream.
        ret: The flag of the last image returned by cap. True means valid.
        img: The latest image from the camera.
        path: path to video used for identification.

    """

    def __init__(self, ID):
        """Initialize the fake camera and make up an image or 2."""
        self.x = 3840
        self.y = 2160
        self.ID = ID
        # self.img = np.zeros((self.y, self.x, 3), dtype=np.uint8)
        self.ret = True
        self.path = "Fake"
        self.loaded_img = cv2.imread('Testing_scan/0.png', -1)
        self.img = self.loaded_img

    def update(self):
        """Get a new FAKE image from the FAKE camera."""
        self.img = self.loaded_img
        return self.ret

    def destroy(self):
        """Shut it down."""
        self.cap.release()
        return


def poll_camera(polled_camera):
    """Update the camera object passed forever."""
    polled_camera.update()
    if polled_camera.ret is True:
        print(polled_camera.path, " connected.")
        while True:
            state = polled_camera.update()
            if state is False:
                print("{} is not returning frames.".format(polled_camera.path))
                print("Exiting.")
                return
    else:
        print(polled_camera.path, " not connecting.")


def refresh_display(refreshed_display):
    """Update the display object passed forever."""
    refreshed_display.refresh_display_forever()
    print("Display Closed, Exiting.")


def motion_detect(polled_camera):
    """Run the motion updating function repeatedly."""
    while True:
        polled_camera.motion_update()


def combine_img_5_to_1(imgs):
    """Combine 5 images into one.

    imgs: A list of numpy images
    Use the following pattern.
    _______________________
    |               |  2  |
    |               |_____|
    |               |  3  |
    |               |_____|
    |       1       |  4  |
    |               |_____|
    |               |  5  |
    |               |_____|
    |_______________|BLCK |
    With the assumption that image 1 is
    3840x2160 and images 2-5 are 640x480.
    If images 2-5 are of size 1280x720 then
    they are automatically resized.
    The returned image is 4480x2160
    """
    work_imgs = []
    for img in imgs:
        if img.shape == (720, 1280, 3):
            work_img = cv2.resize(img,
                                  None,
                                  fx=0.5,
                                  fy=0.666666,
                                  interpolation=cv2.INTER_CUBIC)
            work_imgs.append(work_img)
        else:
            work_img = img.copy()
            work_imgs.append(work_img)

    assert work_imgs[0].shape == (2160, 3840, 3)
    assert work_imgs[1].shape == (480, 640, 3)
    assert work_imgs[2].shape == (480, 640, 3)
    assert work_imgs[3].shape == (480, 640, 3)
    assert work_imgs[4].shape == (480, 640, 3)

    work_imgs.append(np.zeros((240, 640, 3),
                     dtype=np.uint8))
    image_2through5 = np.concatenate(tuple(work_imgs[1:6]), axis=0)
    return np.concatenate((work_imgs[0], image_2through5), axis=1)


def unused_combine_img_5_to_1(imgs):
    """Combine 5 images into one.

    imgs: A list of numpy images
    Use the following pattern.

            1

      2   3   4   5

    With the assumption that image 1 is 1920x1080 and all others are 480x640.
    The returned image is 2560x960
    """
    assert imgs[0].shape == (1080, 1920, 3)
    assert imgs[1].shape == (640, 480, 3)
    assert imgs[2].shape == (640, 480, 3)
    assert imgs[3].shape == (640, 480, 3)
    assert imgs[4].shape == (640, 480, 3)

    image_2through5 = np.concatenate(tuple(imgs[1:5]), axis=1)
    return np.concatenate((imgs[0], image_2through5), axis=0)


def old_combine_img_5_to_1(imgs):
    """Combine 5 images into one.

    imgs: A list of numpy images
    Use the following pattern.
            2    3
       1
            4    5
    With the assumption that image 1 is 1280x960 and all others are 640x480.
    The returned image is 2560x960
    """
    assert imgs[0].shape == (960, 1280, 3)
    assert imgs[1].shape == (480, 640, 3)
    assert imgs[2].shape == (480, 640, 3)
    assert imgs[3].shape == (480, 640, 3)
    assert imgs[4].shape == (480, 640, 3)

    image_2and3 = np.concatenate(tuple(imgs[1:3]), axis=1)
    image_4and5 = np.concatenate(tuple(imgs[3:5]), axis=1)
    image_2345 = np.concatenate((image_2and3, image_4and5), axis=0)
    return np.concatenate((imgs[0], image_2345), axis=1)


def load_graph(model_file):
    """Load a cnn graph from disk according to str 'model_file'."""
    graph = tf.Graph()
    graph_def = tf.GraphDef()
    with open(model_file, "rb") as f:
        graph_def.ParseFromString(f.read())
    with graph.as_default():
        tf.import_graph_def(graph_def)
    return graph


def write_image(img, path):
    """Write the image to the path specified."""
    if path[-3:] == 'png' or path[-3:] == 'PNG':
        t = threading.Thread(target=cv2.imwrite,
                             args=(path,
                                   img,
                                   [cv2.IMWRITE_PNG_COMPRESSION, 10]),
                             daemon=False)
        t.start()
    elif path[-3:] == 'jpg' or path[-3:] == 'JPG':
        t = threading.Thread(target=cv2.imwrite,
                             args=(path,
                                   img,
                                   [cv2.IMWRITE_JPEG_QUALITY, 90]),
                             daemon=False)
        t.start()
    else:
        raise NotImplementedError


def write_image_set(imgs, folder):
    """Write the images to the folder specified."""
    if folder[-1] is not "/":
        folder += "/"
    if not os.path.exists(folder):
        os.makedirs(folder[:-1])
    for index, img in enumerate(imgs):
        t = threading.Thread(target=cv2.imwrite,
                             args=(folder + str(index) + ".png",
                                   imgs[index],
                                   [cv2.IMWRITE_PNG_COMPRESSION,
                                    10]),
                             daemon=False)
        t.start()


def write_scan(drawn_top_img,
               drawn_bot_img,
               raw_top_img,
               raw_bot_img,
               folder,
               gradestring):
    """Write the images to the folder specified."""
    if folder[-1] is not "/":
        folder += "/"
    if not os.path.exists(folder):
        os.makedirs(folder[:-1])
    if not os.path.exists(folder+'raw/'):
        os.makedirs(folder+'raw')
    with open(folder+gradestring, 'wb') as file_to_dump_into:
        pickle.dump(' ', file_to_dump_into)
    combined_drawn_img = np.concatenate((drawn_top_img,
                                         drawn_bot_img),
                                        axis=0)
    combined_raw_img = np.concatenate((raw_top_img,
                                       raw_bot_img),
                                      axis=0)
    t = threading.Thread(target=cv2.imwrite,
                         args=(folder + '0' + ".tif",
                               combined_drawn_img),
                         daemon=False)
    t.start()
    t2 = threading.Thread(target=cv2.imwrite,
                          args=(folder + 'raw/' + '0' + ".tif",
                                combined_raw_img),
                          daemon=False)
    t2.start()
    return combined_drawn_img


def old_write_image(img, path):
    """Write the image to the path specified."""
    cv2.imwrite(path, img,
                [cv2.IMWRITE_PNG_COMPRESSION, 2])


def input_means_GRADENOW(input_bytes_as_ascii):
    """Take a string and decide what it means."""
    if input_bytes_as_ascii == b'0xFF\n':
        return True
    else:
        return False


def compute_diff_measure(img1, img2):
    """Compute the motion metric between the 2 images."""
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    gray1 = cv2.GaussianBlur(gray1, (31, 31), 0)
    gray2 = cv2.GaussianBlur(gray2, (31, 31), 0)
    frame_delta = cv2.absdiff(gray1, gray2)
    thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=1)
    (_, cnts, _) = cv2.findContours(thresh.copy(),
                                    cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
    biggest = 0
    for c in cnts:
        if cv2.contourArea(c) > biggest:
            biggest = cv2.contourArea(c)
    return biggest
