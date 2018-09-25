import os
import shutil
import argparse
import glob
from distutils.dir_util import copy_tree
from subprocess import call
import random


def inplace_replace(filename, old_string, new_string):
    with open(filename) as f:
        s = f.read()
    with open(filename, 'w') as f:
        s = s.replace(old_string, new_string)
        f.write(s)


def mix_folder(root):
    if root[-1] != '/':
        root += '/'
    all_images = glob.glob(root+'*.jpg')
    all_images = [x for x in all_images if os.path.isfile(x[:-4]+'.knots')]
    all_images = [x for x in all_images if os.path.isfile(x[:-4]+'.cant')]

    for image_file in all_images:
        prefix = str(random.randint(0, 9999999999)).zfill(10)

        old = image_file
        new = root+prefix+'.jpg'
        print('Renaming {} to {}'.format(old, new))
        os.rename(old, new)

        old = image_file[:-4]+'.cant'
        new = root+prefix+'.cant'
        print('Renaming {} to {}'.format(old, new))
        os.rename(old, new)

        old = image_file[:-4]+'.knots'
        new = root+prefix+'.knots'
        print('Renaming {} to {}'.format(old, new))
        os.rename(old, new)


ap = argparse.ArgumentParser()
ap.add_argument('-i', '--input_folder',
                required=True,
                help='Folder containing data to train')
args = vars(ap.parse_args())

input_root = args['input_folder']
if input_root[-1] != '/':
    input_root += '/'
if not os.path.exists(input_root):
    print('{} does not exist. Exiting.'.format(input_root))

try:
    shutil.rmtree(input_root+'together')
except FileNotFoundError:
    pass
os.mkdir(input_root+'together')

try:
    shutil.rmtree(input_root+'fine_tuned_models')
except FileNotFoundError:
    pass
os.mkdir(input_root+'fine_tuned_models')

try:
    shutil.rmtree(input_root+'manual_evals')
except FileNotFoundError:
    pass
os.mkdir(input_root+'manual_evals')

try:
    shutil.rmtree('/home/ubuntu/cant-grader/Training_Job/models/train')
except FileNotFoundError:
    pass
os.mkdir('/home/ubuntu/cant-grader/Training_Job/models/train')

try:
    shutil.rmtree('/home/ubuntu/cant-grader/Training_Job/models/eval')
except FileNotFoundError:
    pass
os.mkdir('/home/ubuntu/cant-grader/Training_Job/models/eval')

for record in glob.glob(input_root+'*.record'):
    os.remove(record)

copy_tree(input_root+'base', input_root+'together')
for correction_set in glob.glob(input_root+'correction_set_*/'):
    copy_tree(correction_set, input_root+'together')

mix_folder(input_root+'together')

call(['python',
      '/home/ubuntu/cant-grader/tfrecord_maker.py',
      '-i',
      input_root+'together',
      '-o',
      input_root])

for x in range(5000, 300000, 5000):
    os.chdir('/home/ubuntu/cant-grader/Training_Job')
    shutil.copy(input_root+'inception_custom_pipeline.config',
                '/home/ubuntu/cant-grader/Training_Job/'
                'models/inception_custom_pipeline.config')
    inplace_replace('/home/ubuntu/cant-grader/Training_Job/'
                    'models/inception_custom_pipeline.config',
                    'PATH_TO_TRAIN_FOLDER',
                    input_root)
    inplace_replace('/home/ubuntu/cant-grader/Training_Job/'
                    'models/inception_custom_pipeline.config',
                    'STEPS_TO_TRAIN',
                    str(x))

    print('Running Training Op To Step {}'.format(x))
    call(['python',
          'train.py',
          '--logtostderr',
          '--train_dir=/home/ubuntu/cant-grader/Training_Job/models/train',
          '--pipeline_config_path=models/inception_custom_pipeline.config'])

    try:
        shutil.rmtree('/home/ubuntu/cant-grader/Training_Job/fine_tuned_model')
    except FileNotFoundError:
        pass
    os.chdir('/home/ubuntu/.envs/cant-grader/tensorflow/'
             'models/research/object_detection/')

    print('Running Export Op For Step {}'.format(x))
    call(['python',
          'export_inference_graph.py',
          '--input_type',
          'image_tensor',
          '--output_directory',
          '/home/ubuntu/cant-grader/Training_Job/fine_tuned_model',
          '--pipeline_config_path',
          '/home/ubuntu/cant-grader/Training_Job/'
          'models/inception_custom_pipeline.config',
          '--trained_checkpoint_prefix',
          '/home/ubuntu/cant-grader/Training_Job/'
          'models/train/model.ckpt-'+str(x)])
    shutil.copytree('/home/ubuntu/cant-grader/Training_Job/fine_tuned_model',
                    input_root+'fine_tuned_models/'+str(x))
    os.chdir('/home/ubuntu/cant-grader')

    print('Running Eval Op For Step {}'.format(x))
    call(['python',
          'GRADE.py',
          '-i',
          '/data/All_training_data/Manual_Eval_Baseline/',
          '-o',
          input_root+'manual_evals/'+str(x)+'/'])
