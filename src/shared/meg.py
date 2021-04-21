from psychopy import parallel
from . import config
import time

MEG_MARKERS_ON_FLIP = True

MEG_MARKER_DURATION = .001

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
    start=time.monotonic()
    port.setData(data)
    # hog cpu for accurate timing
    while time.monotonic() < start + MEG_MARKER_DURATION:
        continue
    port.setData(0)  # reset
