FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get -y install gosu swig python3-wxgtk4.0 python3-pip python3-minimal x11-xserver-utils wget qtbase5-dev libsdl2-2.0-0 libusb-1.0-0-dev portaudio19-dev libasound2-dev pulseaudio libpulse-dev\
  && apt-get -y install pkg-config git cmake build-essential nasm wget python3-setuptools libusb-1.0-0-dev  python3-dev python3-pip python3-numpy python3-scipy libglew-dev libtbb-dev \
     libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libavresample-dev ffmpeg x264 x265 libportaudio2 portaudio19-dev \
     python3-opencv libopencv-dev libeigen3-dev \
  && apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
  && apt-get -y install libxml2-dev libglib2.0-dev cmake libusb-1.0-0-dev gobject-introspection \
     libgtk-3-dev gtk-doc-tools  xsltproc libgstreamer1.0-dev \
     libgstreamer-plugins-base1.0-dev libgstreamer-plugins-good1.0-dev \
     libgirepository1.0-dev gettext ninja-build vlc libvlc-dev\
  && apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN wget -O libjpeg-turbo.tar.gz https://sourceforge.net/projects/libjpeg-turbo/files/1.5.1/libjpeg-turbo-1.5.1.tar.gz/download \
  && tar xvzf libjpeg-turbo.tar.gz \
  && cd libjpeg-turbo-1.5.1 \
  && ./configure --enable-static=no --prefix=/usr/local \
  && make install \
  && ldconfig \
  && cd .. \
  && rm -Rf libjpeg*

RUN git clone https://github.com/pupil-labs/libuvc \
  && cd libuvc \
  && mkdir build \
  && cd build \
  && cmake .. \
  && make && make install \
  && cd ../../ && rm -Rf libuvc

RUN mkdir /src/ && cd /src \
  && git clone https://github.com/courtois-neuromod/pupil.git \
  && cd pupil \
  && git checkout testing \
  && pip install -r requirements.txt

ARG ARAVIS_VERSION=0.8.21

RUN pip3 install --upgrade meson numpy scipy ipython pip

# for aravis in docker see https://github.com/AravisProject/aravis/issues/509
RUN cd /src/ \
  && wget https://github.com/AravisProject/aravis/archive/refs/tags/${ARAVIS_VERSION}.tar.gz \
  && tar -xzf ${ARAVIS_VERSION}.tar.gz \
  && cd aravis-$ARAVIS_VERSION \
  && meson build && cd build \
  && ninja && ninja install \
  && cd ../.. && rm -Rf aravis-$ARAVIS_VERSION

COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY pulse-client.conf /etc/pulse/client.conf

RUN chown -R 1000:1000 /src/pupil

ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib/x86_64-linux-gnu

RUN apt-get update \
  && apt-get -y install gdb net-tools\
  && apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-binary :all: --force-reinstall pyzmq

ENV GI_TYPELIB_PATH=/usr/local/lib/x86_64-linux-gnu/girepository-1.0/

ENTRYPOINT ["/entrypoint.sh"]

RUN cd /src/ \
  && wget https://github.com/courtois-neuromod/task_stimuli/archive/refs/heads/eyetracker_desktop.zip \
  && unzip eyetracker_desktop.zip \
  && mv task_stimuli-* task_stimuli
RUN pip3 install -r /src/task_stimuli/requirements.txt
COPY ./.env.docker /src/task_stimuli/.env

RUN pip install python-vlc==3.0.11115

WORKDIR /src/task_stimuli/
