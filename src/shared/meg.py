from psychopy import parallel
from . import config
import time

MEG_MARKERS_ON_FLIP = True

MEG_settings = {
    "TASK_START_CODE": int("00000010", 2),
    "TASK_START_STOP": int("00000100", 2),
    "TASK_FLIP": int("00000101", 2),
}

port = None

def send_signal(data):
    global port
    if not port:
        port = parallel.ParallelPort(address=config.PARALLEL_PORT_ADDRESS)
    port.setData(data)
    time.sleep(0.001)
    port.setData(0)  # reset
