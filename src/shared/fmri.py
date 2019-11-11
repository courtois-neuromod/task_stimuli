from psychopy import core, event, logging
from psychopy.hardware.emulator import launchScan

MR_settings = {
    'TR': 2.000,     # duration (sec) per whole-brain volume
    'sync': '5', # character to use as the sync timing event; assumed to come at start of a volume
    'skip': 0,       # number of volumes lacking a sync pulse at start of scan (for T1 stabilization)
    }

globalClock = core.Clock()

def get_ttl():
    allKeys = event.getKeys([MR_settings['sync']])
    for key in allKeys:
        if key.lower() == MR_settings['sync']:
            return True
    return False
