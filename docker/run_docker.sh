#!/bin/bash
docker run \
  --network host \
  --device=/dev/dri \
  --device=/dev/snd  \
  -v $PWD/src/tasks/videogame.py:/src/task_stimuli/src/tasks/videogame.py \
  -v /run/user/1000/pulse:/run/user/1000/pulse \
  -v $PWD/data:/src/task_stimuli/data\
  -v ~/data/tests/test_docker:/data\
  -e HOST_UID=$(id -u)\
  -e HOST_GID=$(id -g) \
  -e DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e PUPIL_PATH=/src/pupil \
  task_stimuli \
  python3 main.py $@
