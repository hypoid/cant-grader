import glob
import os
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_folder',
                required=True,
                help='Folder containing scans')
ap.add_argument('-o', '--output_folder',
                required=True,
                help='Folder to store training image')
args = vars(ap.parse_args())

input_root = args['input_folder']
output_root = args['output_folder']

if input_root[-1] is not '/':
    input_root += '/'
if output_root[-1] is not '/':
    output_root += '/'
if not os.path.exists(input_root):
    print('Invalid input folder: {}'.format(input_root))
    exit()
if not os.path.exists(output_root):
    os.mkdir(output_root)

for scan in os.listdir(input_root):
    has_knots = False
    for imagename in glob.glob(input_root+scan+'/*.png'):
        if os.path.isfile(imagename+'.knots'):
            has_knots = True
    if has_knots is True:
        os.rename(input_root+scan, output_root+scan)
        print("Moving {} to {}.".format(input_root+scan, output_root+scan))
