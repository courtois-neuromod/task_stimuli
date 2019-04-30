from psychopy import parallel
from . import config

def send_signal(data):
    port = parallel.ParallelPort(address=config.PARALLEL_PORT_ADDRESS)
    port.setData(data)
    port.setData(0) #reset
