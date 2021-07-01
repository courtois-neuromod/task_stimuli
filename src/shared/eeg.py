from psychopy import parallel
from . import config
import time

# ensure the port is reset at launch
port = parallel.ParallelPort(address=config.PARALLEL_PORT_ADDRESS)
port.setPin(6, 0)

def send_spike():
    # port = parallel.ParallelPort(address=config.PARALLEL_PORT_ADDRESS)
    port.setPin(6, 1)
    # port.setData(data)
    # time.sleep(0.001)
    time.sleep(0.5)
    port.setPin(6, 0)
    #port.setData(0)  # reset
