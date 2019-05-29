from psychopy import parallel
from . import config
import time

def send_signal(data):
    port = parallel.ParallelPort(address=config.PARALLEL_PORT_ADDRESS)
    port.setData(data)
    time.sleep(1)
    port.setData(0) #reset
