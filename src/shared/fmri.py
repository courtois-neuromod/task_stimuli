from psychopy import core, event, logging
from psychopy.hardware.emulator import launchScan

MR_settings = {
    'TR': 2.000,     # duration (sec) per whole-brain volume
    'volumes': 5,    # number of whole-brain 3D volumes per scanning run
    'sync': '5', # character to use as the sync timing event; assumed to come at start of a volume
    'skip': 0,       # number of volumes lacking a sync pulse at start of scan (for T1 stabilization)
    'sound': True    # in test mode: play a tone as a reminder of scanner noise
    }

globalClock = core.Clock()

def wait_for_ttl(window):
    while True:
        allKeys = event.getKeys()
        for key in allKeys:
            if key == MR_settings['sync']:
                window.logOnFlip(
                    level=logging.EXP,
                    msg="fMRI TTL")
                return True
