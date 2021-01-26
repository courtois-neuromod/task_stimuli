FROM ubuntu:20.04

RUN export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get -y install python3-pip python3-minimal x11-xserver-utils wget qtbase5-dev libsdl2-2.0-0\
  && apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . /src/task_stimuli

RUN pip3 install -r /src/task_stimuli/requirements.txt

RUN wget -O /tmp/antimicrox.deb 'https://github.com/AntiMicroX/antimicrox/releases/download/3.1.4/antimicrox-3.1.4-x86_64.deb' \
  && dpkg -i /tmp/antimicrox.deb \
  && rm /tmp/antimicrox.deb

ENTRYPOINT ["python3", "/src/task_stimuli/main.py"]
