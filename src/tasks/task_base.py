from psychopy import logging

from ..shared import fmri

class Task(object):

    def __init__(self,use_fmri=False, use_eyetracking=False):
        self.use_fmri = use_fmri
        self.use_eyetracking = use_eyetracking

    # preload large files for accurate start with other recordings (scanner, biopac...)
    def preload(self, exp_win):
        pass

    def unload(self):
        pass

    def run(self, exp_win, ctl_win):
        if hasattr(self, 'instructions'):
            for _ in self.instructions(ctl_win, ctl_win):
                exp_win.flip()
                ctl_win.flip()

        if self.use_fmri:
            ttl_index = 0
            while True:
                if fmri.get_ttl():
                    #TODO: log real timing of TTL?
                    exp_win.logOnFlip(
                        level=logging.EXP,
                        msg="fMRI TTL %d"%ttl_index)
                    ttl_index += 1
                    break
                yield()
        for _ in self._run(exp_win, ctl_win):
            if self.use_fmri:
                if fmri.get_ttl():
                    exp_win.logOnFlip(
                        level=logging.EXP,
                        msg="fMRI TTL %d"%ttl_index)
                    ttl_index += 1
            yield()
