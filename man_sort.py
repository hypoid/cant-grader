"""Sort the files based on user input."""

import cv2
import os
import glob
import argparse
import shutil

ap = argparse.ArgumentParser()
ap.add_argument("-f", "--folder", required=True, help="Folder to sort")
ap.add_argument("-s", "--start",
                nargs='?',
                const=1,
                help="Start image #",
                type=int)
args = vars(ap.parse_args())
path = args["folder"]
start = args["start"]

if path[-1] is not "/":
    path += "/"
if not os.path.exists(path):
    print("Invalid path: {}".format(path))
    exit()
if not os.path.exists(path + "True"):
    os.makedirs(path + "True")
if not os.path.exists(path + "False"):
    os.makedirs(path + "False")

font = cv2.FONT_HERSHEY_SIMPLEX
if start is None:
    start = 1
i = start
filenames = glob.glob(path+"*.png")
file_lables = []
for filename in filenames:
    file_lables.append(0)

while True:
    print("Current image number is: "+str(i))
    img = cv2.imread(filenames[i], -1)
    if file_lables[i] is 1:
        cv2.putText(img, ("Labled as 'True'"),
                    (20, 40), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
    if file_lables[i] is -1:
        cv2.putText(img, ("Labled as 'False'"),
                    (10, 40), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imshow(("Is it clear? Right Shift = True,"
                "? = False, Enter = Finalize, "
                "- = Go back, + = Go forward"),
               img[::2, ::2, ::])
    k = cv2.waitKey(0) & 0xFF
    if k == 45 and i > 0:
        i -= 1
    if k == 61 and i < (len(filenames) - 1):
        i += 1
    if k == 226:
        file_lables[i] = 1
        if i < (len(filenames) - 1):
            i += 1
    if k == 47:
        file_lables[i] = -1
        if i < (len(filenames) - 1):
            i += 1
    print(k)
    if k == 27:
        exit()
    if k == 13:
        break
for index, filename in enumerate(filenames):
    TruePath = filename.replace(path, path+"True/")
    FalsePath = filename.replace(path, path+"False/")
    if file_lables[index] > 0:
        print("Copying {} to {}".format(filename, TruePath))
        shutil.copyfile(filename, TruePath)
    if file_lables[index] < 0:
        print("Copying {} to {}".format(filename, FalsePath))
        shutil.copyfile(filename, FalsePath)
