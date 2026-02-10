#!/bin/bash
docker run \
  --network host \
  --device=/dev/dri \
  --device=/dev/snd  \
  -v $PWD/src/:/src/task_stimuli/src/ \
  -v /run/user/$(id -u)/pulse:/run/user/$(id -u)/pulse \
  -v $PWD/data:/src/task_stimuli/data\
  -v ~/data/tests/test_docker:/data\
  -e HOST_UID=$(id -u)\
  -e HOST_GID=$(id -g) \
  -e DISPLAY \
  -e XAUTHORITY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v ${XAUTHORITY}:${XAUTHORITY} \
  -e PUPIL_PATH=/src/pupil \
  -it \
  task_stimuli \
  python3 main.py $@
