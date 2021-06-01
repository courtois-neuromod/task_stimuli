from psychopy import core, event, logging
from psychopy.hardware.emulator import launchScan
import time

MR_settings = {
    "TR": 2.000,  # duration (sec) per whole-brain volume
    "sync": "5",  # character to use as the sync timing event; assumed to come at start of a volume
    "skip": 0,  # number of volumes lacking a sync pulse at start of scan (for T1 stabilization)
}

globalClock = core.Clock()


def get_ttl():
    allKeys = event.getKeys([MR_settings["sync"]])
    for key in allKeys:
        if key.lower() == MR_settings["sync"]:
            return True
    return False


# blocking function (iterator)
def wait_for_ttl():
    get_ttl()  # flush any remaining TTL keys
    ttl_index = 0
    logging.exp(msg="waiting for fMRI TTL")
    while True:
        if get_ttl():
            # TODO: log real timing of TTL?
            logging.exp(msg="fMRI TTL %d" % ttl_index)
            ttl_index += 1
            return
        time.sleep(0.0005)  # just to avoid looping to fast
        yield


SCANNER_TRIGGER = {
    'start': 5,
    'stop': 0
}
DEVICE_NAME = '/dev/serial/by-id/usb-SparkFun_SparkFun_Pro_Micro-if00'

def trigger_scanner(signal):
    if signal in SCANNER_TRIGGER.keys():
        with open(DEVICE_NAME,'w') as f:
            f.write(str(SCANNER_TRIGGER[signal]))
            logging.info(f"sent {signal} to scanner")
    else:
        raise ValueError('Unknown scanner signal')
