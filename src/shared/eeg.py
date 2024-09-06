import serial
from . import config
import time

EEG_MARKERS_ON_FLIP = True

EEG_MARKER_DURATION = .001

EEG_settings = {
    "TASK_START_CODE": int("00000001", 2),
    "TASK_STOP_CODE": int("00000001", 2),
    "TASK_FLIP": int("000000010", 2),
}

port = None
current_signal = 0
reset = 0

def send_signal(data):
    global port
    if not port:
        port = serial.Serial(config.SERIAL_PORT_ADDRESS)
    start=time.monotonic()
    port.write(data.to_bytes(1, byteorder='big'))
    # hog cpu for accurate timing
    while time.monotonic() < start + EEG_MARKER_DURATION:
        continue
    port.write(reset.to_bytes(1, byteorder='big'))  # reset


def set_trigger_signal():
    global port, current_signal
    if not port:
        port = serial.Serial(config.SERIAL_PORT_ADDRESS)
    new_signal = 0 if current_signal else EEG_settings["TASK_FLIP"]
    port.write(new_signal.to_bytes(1, byteorder='big'))
    current_signal = new_signal
