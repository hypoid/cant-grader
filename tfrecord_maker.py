"""Convert scans and bounding boxes to a training TFRecord."""

import cv2
import argparse
import os
import glob
import pickle
import sys
import traceback
import pdb
import tensorflow as tf
from object_detection.utils import dataset_util

eval_percentage = 0.01
size = 300


def info(type, value, tb):
    """Start the debugger if we run into an exception."""
    traceback.print_exception(type, value, tb)
    pdb.pm()


sys.excepthook = info

ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_folder',
                required=True,
                help='Folder containing scans')
ap.add_argument('-o', '--output_file',
                required=True,
                help='Folder to store training image')
ap.add_argument('-c', '--camera',
                required=False,
                type=int,
                help='Camera')
args = vars(ap.parse_args())

input_root = args['input_folder']
output_path = args['output_file']
cam_num = args['camera']

if input_root[-1] is not '/':
    input_root += '/'
if not os.path.exists(input_root):
    print('Invalid input folder: {}'.format(input_root))
    exit()


imagenames = glob.glob(input_root+'*.jpg')
imagenames = [x for x in imagenames if os.path.isfile(x[:-4]+'.knots')]
imagenames = [x for x in imagenames if os.path.isfile(x[:-4]+'.cant')]

eval_writer = tf.python_io.TFRecordWriter(output_path+'eval.record')
train_writer = tf.python_io.TFRecordWriter(output_path+'train.record')
# For each camera image therein
for index, imagename in enumerate(imagenames):
    # If the image isn't annotated with defect bounding boxes
    # then we skip it
    if not os.path.isfile(imagename[:-4]+'.knots'):
        continue
    if not os.path.isfile(imagename[:-4]+'.cant'):
        continue
    print('Processing {}'.format(imagename))
    image = cv2.imread(imagename, -1)
    if image is None:
        continue

    # Start packaging for TFRecord
    width = image.shape[1]
    height = image.shape[0]
    filename = imagename.encode('UTF8')
    with tf.gfile.GFile(imagename, 'rb') as file_id:
        encoded_image_data = file_id.read()
    image_format = b'jpg'

    xmins = []
    xmaxs = []
    ymins = []
    ymaxs = []
    classes_text = []
    classes = []

    # Load the bounding boxes from disk
    knots = pickle.load(open(imagename[:-4]+'.knots', 'rb'))
    cants = pickle.load(open(imagename[:-4]+'.cant', 'rb'))
    for box in knots:
        if box.xmin == box.xmax:
            continue
        if box.ymin == box.ymax:
            continue
        if box.ymax < box.ymin:
            true_min = box.ymax
            true_max = box.ymin
            box.ymin = true_min
            box.ymax = true_max
        if box.xmax < box.xmin:
            true_min = box.xmax
            true_max = box.xmin
            box.xmin = true_min
            box.xmax = true_max
        if box.xmin > size-1:
            box.xmin = size-1
        if box.xmax > size-1:
            box.xmax = size-1
        if box.ymin > size-1:
            box.ymin = size-1
        if box.ymax > size-1:
            box.ymax = size-1
        if box.xmin < 1:
            box.xmin = 1
        if box.xmax < 1:
            box.xmax = 1
        if box.ymin < 1:
            box.ymin = 1
        if box.ymax < 1:
            box.ymax = 1
        assert box.xmin < box.xmax
        assert box.ymin < box.ymax
        assert box.xmin < size
        assert box.xmax < size
        assert box.ymin < size
        assert box.ymax < size
        assert box.xmin > 0
        assert box.xmax > 0
        assert box.ymin > 0
        assert box.ymax > 0
        xmins.append(box.xmin/width)
        xmaxs.append(box.xmax/width)
        ymins.append(box.ymin/height)
        ymaxs.append(box.ymax/height)
        classes_text.append(b'knot')
        classes.append(1)
    for box in cants:
        if box.xmin == box.xmax:
            continue
        if box.ymin == box.ymax:
            continue
        if box.ymax < box.ymin:
            true_min = box.ymax
            true_max = box.ymin
            box.ymin = true_min
            box.ymax = true_max
        if box.xmax < box.xmin:
            true_min = box.xmax
            true_max = box.xmin
            box.xmin = true_min
            box.xmax = true_max
        if box.xmin > size-1:
            box.xmin = size-1
        if box.xmax > size-1:
            box.xmax = size-1
        if box.ymin > size-1:
            box.ymin = size-1
        if box.ymax > size-1:
            box.ymax = size-1
        if box.xmin < 1:
            box.xmin = 1
        if box.xmax < 1:
            box.xmax = 1
        if box.ymin < 1:
            box.ymin = 1
        if box.ymax < 1:
            box.ymax = 1
        assert box.xmin < box.xmax
        assert box.ymin < box.ymax
        assert box.xmin < size
        assert box.xmax < size
        assert box.ymin < size
        assert box.ymax < size
        assert box.xmin > 0
        assert box.xmax > 0
        assert box.ymin > 0
        assert box.ymax > 0
        xmins.append(box.xmin/width)
        xmaxs.append(box.xmax/width)
        ymins.append(box.ymin/height)
        ymaxs.append(box.ymax/height)
        classes_text.append(b'cant')
        classes.append(2)

    tf_example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(filename),
        'image/source_id': dataset_util.bytes_feature(filename),
        'image/encoded': dataset_util.bytes_feature(encoded_image_data),
        'image/format': dataset_util.bytes_feature(image_format),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmins),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmaxs),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymins),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymaxs),
        'image/object/class/text': dataset_util.bytes_list_feature(
            classes_text),
        'image/object/class/label': dataset_util.int64_list_feature(classes),
        }))
    if index <= (len(imagenames) * eval_percentage):
        eval_writer.write(tf_example.SerializeToString())
    else:
        train_writer.write(tf_example.SerializeToString())
eval_writer.close()
train_writer.close()
print("{}train.record written.".format(output_path))
print("{}eval.record written.".format(output_path))
