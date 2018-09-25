import glob
import os
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_folder',
                required=True,
                help='Folder containing scans')
args = vars(ap.parse_args())
input_dir = args['input_folder']
if input_dir[-1] != '/':
    input_dir += '/'
for filename in glob.glob(input_dir+'*.png'):
    if os.path.isfile(filename[:-4]+'.knots'):
        continue
    if os.path.isfile(filename+'.knots'):
        old = filename+'.knots'
        new = filename[:-4]+'.knots'
        print("Renaming {} to {}".format(old, new))
        os.rename(old, new)
