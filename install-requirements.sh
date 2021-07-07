#!/usr/bin/env bash
#
# install dependencies for conda with python 3.6.9

set -ex

conda create --name task_stimuli python=3.6.9
conda activate task_stimuli

# Not working:
#echo $(curl https://raw.githubusercontent.com/wxWidgets/Phoenix/wxPy-4.0.x/vagrant/ubuntu-18.04/bootstrap.sh) | bash
# might be working: https://www.programmersought.com/article/80326948951/

# Not working:
# @warning requires sudo!
# # cf. https://www.psychopy.org/download.html
# sudo echo 'deb http://cz.archive.ubuntu.com/ubuntu bionic main universe' > /etc/apt/sources.list.d/task_stimuli_bionic.list
# # cf https://stackoverflow.com/questions/62301866/how-to-install-the-libwebkitgtk-package-on-ubuntu-20-04-lts
# sudo apt update
# sudo apt install libwebkitgtk-1.0
# sudo rm /etc/apt/sources.list.d/task_stimuli_bionic.list
# sudo apt update

# sudo apt install libusb-1.0-0-dev portaudio19-dev libasound2-dev

# Not working:
# tmpdir=$(mktemp -d)
# psychopy_env_path=$tmpdir/psychopy-env.yml
# curl https://raw.githubusercontent.com/psychopy/psychopy/master/conda/psychopy-env.yml > $psychopy_env_path
# conda env update --file $psychopy_env_path
# rm -r $tmpdir

# Not working:
# conda install --yes -c conda-forge psychopy>=2020.2.4.post1  # hanging forever

# Not working:
# pip install psychopy>=2020.2.4.post1

conda install -c anaconda portaudio
conda install -c anaconda wxpython

conda install --yes pip
# Not working (wheel uncompatible with python3.6)
# @ERROR MUST UPGRADE URL!! https://extras.wxpython.org/wxPython4/extras/linux/gtk3/
# python3.6 -m pip install https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/wxPython-4.1.1-cp38-cp38-linux_x86_64.whl

python3.6 -m pip install psychopy

conda install --yes numpy

conda install --yes colorama
conda install --yes pandas>=1.1.1
conda install --yes -c conda-forge python-dotenv
conda install --yes tqdm>=4.60.0
conda install --yes textdistance

pip install git+https://github.com/pyserial/pyparallel

