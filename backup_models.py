
import argparse
import os
import time
import shutil


ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_folder',
                required=True,
                help='Folder containing scans')
ap.add_argument('-o', '--output_folder',
                required=True,
                help='Folder to store training image')
ap.add_argument('-t', '--time',
                required=False,
                type=int,
                help='time to make backups')
args = vars(ap.parse_args())

input_root = args['input_folder']
output_root = args['output_folder']
time_to_copy = args['time']
if time_to_copy is None:
    time_to_copy = 20000

if input_root[-1] is not '/':
    input_root += '/'
if output_root[-1] is not '/':
    output_root += '/'
if not os.path.exists(input_root):
    print('Invalid input folder: {}'.format(input_root))
    exit()
if not os.path.exists(output_root):
    os.mkdir(output_root)

start_time = time.time()
while True:
    if (time.time() - start_time) > time_to_copy:
        break
    date_time = time.strftime("%Y%m%d%H%M%S")
    print('Saving:'+date_time)
    shutil.copytree(input_root+'/train', '{}{}/train'.format(output_root,
                                                             date_time))
    shutil.copytree(input_root+'/eval', '{}{}/eval'.format(output_root,
                                                           date_time))
    time.sleep(1000)
