from psychopy import core, event, logging
import time
from . import utils

MR_settings = {
    "TR": 2.000,  # duration (sec) per whole-brain volume
    "sync": ["5", "percent", "t", "T"],  # character to use as the sync timing event; assumed to come at start of a volume
    "skip": 0,  # number of volumes lacking a sync pulse at start of scan (for T1 stabilization)
}

globalClock = core.Clock()


def get_ttl():
    utils.poll_windows()
    allKeys = event.getKeys(MR_settings["sync"])
    for key in allKeys:
        if key.lower() in MR_settings["sync"]:
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
