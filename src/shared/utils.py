import psutil
import time
from psychopy import core, logging
import os, glob
from inspect import getframeinfo, stack

def check_power_plugged():
    battery = psutil.sensors_battery()
    if battery:
        return battery.power_plugged
    else:
        return True

def wait_until(clock, deadline, hogCPUperiod=0.1, keyboard_accuracy=.0005):
    if deadline < clock.getTime():
        caller = getframeinfo(stack()[1][0])
        logging.error(f'wait_until called after deadline: {deadline} < {clock.getTime()} {caller.filename}:{caller.lineno}')
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

def wait_until_yield(clock, deadline, hogCPUperiod=0.1, keyboard_accuracy=.0005):
    if deadline < clock.getTime():
        caller = getframeinfo(stack()[1][0])
        logging.error(f'wait_until called after deadline: {deadline} < {clock.getTime()} {caller.filename}:{caller.lineno}')
    sleep_until = deadline - hogCPUperiod
    poll_windows()
    current_time = clock.getTime()
    while current_time < deadline:
        if current_time < sleep_until:
            time.sleep(keyboard_accuracy)
            yield

        poll_windows()
        current_time = clock.getTime()

def get_subject_soundcheck_video(subject):
    setup_video_path = glob.glob(
        os.path.join("data", "videos", "subject_setup_videos", "sub-%s_*" % subject)
    )
    if not len(setup_video_path):
        return os.path.join(
                "data",
                "videos",
                "subject_setup_videos",
                "sub-default_setup_video.mp4",
            )
    return setup_video_path[0]
