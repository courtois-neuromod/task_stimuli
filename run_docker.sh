#!/bin/bash
sudo docker run \
  --network host \
  --device=/dev/dri \
  --device=/dev/snd  \
  -v $PWD/src:/src/task_stimuli/src \
  -v /run/user/1000/pulse:/run/user/1000/pulse \
  -v $PWD/data:/src/task_stimuli/data\
  -e HOST_UID=$(id -u)\
  -e HOST_GID=$(id -g) \
  -e DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  task_stimuli \
  python3 main.py $@
