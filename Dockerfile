FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get -y install gosu swig python3-wxgtk4.0 python3-pip python3-minimal x11-xserver-utils wget qtbase5-dev libsdl2-2.0-0 libusb-1.0-0-dev portaudio19-dev libasound2-dev pulseaudio libpulse-dev\
  && apt-get -y install pkg-config git cmake build-essential nasm wget python3-setuptools libusb-1.0-0-dev  python3-dev libglew-dev libtbb-dev \
     libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libavresample-dev ffmpeg x264 x265 libportaudio2 portaudio19-dev \
     python3-opencv libopencv-dev libeigen3-dev \
  && apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
  && apt-get -y install libxml2-dev libglib2.0-dev cmake libusb-1.0-0-dev gobject-introspection \
     libgtk-3-dev gtk-doc-tools  xsltproc libgstreamer1.0-dev \
     libgstreamer-plugins-base1.0-dev libgstreamer-plugins-good1.0-dev \
     libgirepository1.0-dev gettext ninja-build vlc libvlc-dev\
  && apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip 

RUN pip3 install "numpy<1.24" meson scipy

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY docker/pulse-client.conf /etc/pulse/client.conf

ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib/x86_64-linux-gnu

RUN apt-get update \
  && apt-get -y install gdb net-tools\
  && apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-binary :all: --force-reinstall pyzmq

ENV GI_TYPELIB_PATH=/usr/local/lib/x86_64-linux-gnu/girepository-1.0/

ENTRYPOINT ["/entrypoint.sh"]

COPY ./ /src/task_stimuli
RUN pip3 install -r /src/task_stimuli/requirements.txt
COPY docker/.env.docker /src/task_stimuli/.env

RUN pip3 install python-vlc==3.0.11115

WORKDIR /src/task_stimuli/
