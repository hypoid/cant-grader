# Installation


#### Install virtualenv
'''
sudo pip install virtualenv
'''

#### Install the virtual environment for isolation
'''
virtualenv --python=/usr/bin/python3 ~/.envs/cant-grader
'''

#### Install git
'''
sudo apt install git
'''

#### Initially get the project from github
'''
cd ~

git clone https://github.com/hypoid/cant-grader.git

cd cant-grader
'''

#### Activated the virtualenv
'''
source ~/.envs/cant-grader/bin/activate
'''

#### Make it so that the virtualenv is activated for you
'''
echo 'source ~/.envs/cant-grader/bin/activate' >> ~/.bashrc
'''

#### Install python libraries
'''
pip install -r requirements.txt
'''

#### Make it so that you don't have to enter user/password all the time
'''
git config credential.helper store
'''

#### Download the tensorflow helper scripts and pre-trained models
'''
cd ~/.envs/cant-grader
git clone https://github.com/tensorflow/tensorflow.git
cd ~/.envs/cant-grader/tensorflow
git clone https://github.com/tensorflow/models/
'''

#### Get protoc for Protobuf compilation
'''
cd ~/.envs/cant-grader/tensorflow
mkdir protoc_3.3
cd protoc_3.3
wget https://github.com/google/protobuf/releases/download/v3.3.0/protoc-3.3.0-linux-x86_64.zip
chmod 775 protoc-3.3.0-linux-x86_64.zip
unzip protoc-3.3.0-linux-x86_64.zip
cd ../models/research
~/.envs/cant-grader/tensorflow/protoc_3.3/bin/protoc object_detection/protos/*.proto --python_out=.
'''

#### Add these to the PYTHONPATH
'''
cd ~/.envs/cant-grader/tensorflow/models/research
export PYTHONPATH=$PYTHONPATH:`pwd`:`pwd`/slim
'''

#### Make it permenant
'''
echo 'export PYTHONPATH=$PYTHONPATH:~/.envs/cant-grader/tensorflow/models/research:~/.envs/cant-grader/tensorflow/models/research/slim' >> ~/.bashrc
'''

#### Protobuf Compilation
'''
cd ~/.envs/cant-grader/tensorflow/models/research/
protoc object_detection/protos/*.proto --python_out=.
'''

### Test it
'''
python object_detection/builders/model_builder_test.py
'''

#### Install COCO mpa tools
'''
sudo apt-get install python3-tk
cd ~
git clone https://github.com/cocodataset/cocoapi.git
cd cocoapi/PythonAPI
make
cp -r pycocotools <path_to_tensorflow>/models/research/
'''

# Commands used as needed:

#### Add to repo
'''
git add FILENAME
'''

#### To push back:
'''
git commit -a -m "Commit message"
'''

'''
git push origin master
'''

#### To get an updated copy from GitHub
'''
git pull origin
'''

#### Cusom adjustments to training scripts:
~/.envs/cant-grader/tensorflow/models/research/object_detection/trainer.py line 357
from this:
'''
    slim.learning.train(
        train_tensor,
        logdir=train_dir,
        master=master,
        is_chief=is_chief,
        session_config=session_config,
        startup_delay_steps=train_config.startup_delay_steps,
        init_fn=init_fn,
        summary_op=summary_op,
        number_of_steps=(
            train_config.num_steps if train_config.num_steps else None),
        save_summaries_secs=120,
        sync_optimizer=sync_optimizer,
        saver=saver)
'''

to this:
'''
    slim.learning.train(
        train_tensor,
        logdir=train_dir,
        master=master,
        is_chief=is_chief,
        session_config=session_config,
        startup_delay_steps=train_config.startup_delay_steps,
        init_fn=init_fn,
        summary_op=summary_op,
        number_of_steps=(
            train_config.num_steps if train_config.num_steps else None),
        save_summaries_secs=100,
        save_interval_secs=100,
        max_to_keep10=2000,
        sync_optimizer=sync_optimizer,
        saver=saver)
'''
