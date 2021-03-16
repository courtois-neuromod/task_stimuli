import psutil
import time
from psychopy import core


def check_power_plugged():
    battery = psutil.sensors_battery()
    if battery:
        return battery.power_plugged
    else:
        return True

def wait_until(clock, deadline, hogCPUperiod=0.1, keyboard_accuracy=.0005):
    sleep_until = deadline - hogCPUperiod
    poll_windows()
    current_time = clock.getTime()
    while current_time < deadline:
        if current_time < sleep_until:
            time.sleep(keyboard_accuracy)
        poll_windows()
        current_time = clock.getTime()

def poll_windows():
    for winWeakRef in core.openWindows:
        win = winWeakRef()
        if (win.winType == "pyglet" and
                hasattr(win.winHandle, "dispatch_events")):
            win.winHandle.dispatch_events()  # pump events
