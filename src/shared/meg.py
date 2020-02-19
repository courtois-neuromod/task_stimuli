from psychopy import parallel
from . import config
import time

# general triggers, common to every MEG protocoles
MEG_settings = {
    'TASK_START_CODE': int("00000010", 2),
    'TASK_STOP_CODE': int("00000100", 2),
}

# triggers for the eye-movements task
MEG_eyemvt = {
    'sacc_left': int('10000000', 2),
    'sacc_right': int('01000000', 2),
    'sacc_up': int('00100000', 2),
    'sacc_down': int('00010000', 2),
    'SP_left': int('10000001', 2),
    'SP_right': int('01000001', 2),
    'SP_up': int('00100001', 2),
    'SP_down': int('00010001', 2)
}

def send_signal(data):
    port = parallel.ParallelPort(address=config.PARALLEL_PORT_ADDRESS)
    port.setData(data)
    time.sleep(0.001)
    port.setData(0) #reset
