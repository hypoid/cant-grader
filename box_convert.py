"""Convert old boxes to new boxes."""
import pickle
import os
import glob
import cv2

import argparse
import detect_cants_and_knots

font = cv2.FONT_HERSHEY_SIMPLEX


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

    def draw(self, img, color=(0, 255, 0), draw_probability=False):
        if draw_probability is True:
            cv2.putText(img,
                        str(self.score),
                        (self.xmin, self.ymin-10),
                        font,
                        1,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA)
        cv2.rectangle(img,
                      (self.xmin, self.ymin),
                      (self.xmax, self.ymax),
                      color,
                      2)


ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_folder',
                required=True,
                help='Folder containing scans')
ap.add_argument('-o', '--output_folder',
                required=True,
                help='Folder to send converted boxes to')
ap.add_argument('-t', '--filetype',
                required=True,
                help='File extension to look for, e.g. .knots or .cant')

args = vars(ap.parse_args())

output_root = args['output_folder']
if output_root[-1] is not '/':
    output_root += '/'
if not os.path.exists(output_root):
    os.mkdir(output_root)

input_root = args['input_folder']
if input_root[-1] is not '/':
    input_root += '/'
if not os.path.exists(input_root):
    print('Invalid input folder: {}'.format(input_root))
    exit()

ftype = args['filetype']

filenames = glob.glob(input_root+'*'+ftype)

for filename in filenames:
    print('Opening {}'.format(filename))
    with open(filename, 'rb') as fid:
        boxes = pickle.load(fid)
    new_boxes = []
    for box in boxes:
        new_boxes.append(detect_cants_and_knots.Box(box.ymin,
                                                    box.xmin,
                                                    box.ymax,
                                                    box.xmax,
                                                    box.score))
    new_filename = output_root+filename[filename.rfind('/')+1:]
    with open(new_filename, 'wb') as fid:
        pickle.dump(new_boxes, fid)
        print('Saved {}'.format(new_filename))
