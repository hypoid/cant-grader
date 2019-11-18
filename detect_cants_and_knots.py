"""A little class to handle finding knots."""
import os
import tensorflow as tf
import numpy as np
import cv2
import glob
import time


font = cv2.FONT_HERSHEY_SIMPLEX


class knot_finder(object):
    """Class to hold knot finder attributes."""
    def __init__(self, path):
        """Setup the knot finder"""
        # path = ('Training_Job/'
        #        'fine_tuned_model/'
        #        'frozen_inference_graph.pb')
        if path is None:
            PATH_TO_MODEL = ('Production_Graphs/'
                             'fine_tuned_model_production/'
                             'frozen_inference_graph.pb')
        else:
            PATH_TO_MODEL = path
        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(PATH_TO_MODEL, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
            with tf.device('/device:GPU:1'):
                self.image_tensor = self.detection_graph.get_tensor_by_name(
                    'image_tensor:0')
                self.d_boxes = self.detection_graph.get_tensor_by_name(
                    'detection_boxes:0')
                self.d_scores = self.detection_graph.get_tensor_by_name(
                    'detection_scores:0')
                self.d_classes = self.detection_graph.get_tensor_by_name(
                    'detection_classes:0')
                self.num_d = self.detection_graph.get_tensor_by_name(
                    'num_detections:0')
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        self.sess = tf.Session(graph=self.detection_graph,config=config)

    def get_cant_and_knots(self, img):
        """Find bounding boxes for all of the knots in the image 'img'."""
        with self.detection_graph.as_default():
            # Expand dimension since the model expects image to have
            # shape [1, None, None, 3].
            img_expanded = np.expand_dims(img, axis=0)
            (boxes, scores, classes, num) = self.sess.run(
                [self.d_boxes, self.d_scores, self.d_classes, self.num_d],
                feed_dict={self.image_tensor: img_expanded})
            cants = []
            knots = []
            height = img.shape[0]
            width = img.shape[1]
            for indx, box in enumerate(boxes[0]):
                if scores[0][indx] > 0.10:
                    if classes[0][indx] == 1:
                        knots.append(Box(int(box[0]*height),
                                         int(box[1]*width),
                                         int(box[2]*height),
                                         int(box[3]*width),
                                         scores[0][indx]))
                    if classes[0][indx] == 2:
                        cants.append(Box(int(box[0]*height),
                                         int(box[1]*width),
                                         int(box[2]*height),
                                         int(box[3]*width),
                                         scores[0][indx]))
        return cants, knots


class Box(object):
    """A simple box object."""
    def __init__(self, ymin, xmin, ymax, xmax, score=1):
        """Define a box object."""
        self.ymin = ymin
        self.xmin = xmin
        self.ymax = ymax
        self.xmax = xmax
        self.score = score
        self.area = abs(xmin-xmax)*abs(ymin-ymax)

    def __repr__(self):
        return "Box({}, {}, {}, {}, score={})".format(self.ymin,
                                                      self.xmin,
                                                      self.ymax,
                                                      self.xmax,
                                                      self.score)

    def draw(self, img, color=(0, 255, 0), draw_probability=True):
        if draw_probability is True:
            cv2.putText(img,
                        str(round(self.score, 4)),
                        (self.xmin, self.ymin-3),
                        font,
                        1,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA)
        cv2.rectangle(img,
                      (self.xmin, self.ymin),
                      (self.xmax, self.ymax),
                      color,
                      3)


if __name__ == '__main__':
    files = glob.glob('/data/All_training_data/Fully_'
                      'Labled/20180404/cant_and_knots/*.jpg')
    finder = knot_finder()
    start_time = time.time()
    i = 0
    for fname in files:
        image_to_test = cv2.imread((fname), -1)
        work_img = image_to_test.copy()
        width = float(work_img.shape[1])
        height = float(work_img.shape[0])
        cants, knots = finder.get_cant_and_knots(image_to_test)
        for cant in cants:
            cant.draw(work_img)
        for knot in knots:
            knot.draw(work_img, color=(0, 0, 255))
        i += 1
        cv2.imshow('image', work_img)
        k = cv2.waitKey(1) & 0xFF
        if k == 27:
            print('Operation Canceled By User')
            break
    print('{} Seconds used to process {} images.'.format(
        time.time()-start_time, i))
    print(i/(time.time()-start_time), 'fps')
