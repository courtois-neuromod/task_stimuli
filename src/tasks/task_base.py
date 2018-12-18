from psychopy import logging, visual

from ..shared import fmri

class Task(object):

    def __init__(self, name, use_fmri=False, use_eyetracking=False):
        self.name = name
        self.use_fmri = use_fmri
        self.use_eyetracking = use_eyetracking

    # preload large files for accurate start with other recordings (scanner, biopac...)
    def preload(self, exp_win):
        pass

    def unload(self):
        pass

    def __str__(self):
        return '%s : %s'%(self.__class__, self.name)

    def run(self, exp_win, ctl_win):
        print('Next task: %s'%str(self))
        if hasattr(self, 'instructions'):
            for _ in self.instructions(exp_win, ctl_win):
                exp_win.flip()
                ctl_win.flip()

        if self.use_fmri:
            ttl_index = 0
            while True:
                if fmri.get_ttl():
                    #TODO: log real timing of TTL?
                    logging.exp(msg="fMRI TTL %d"%ttl_index)
                    ttl_index += 1
                    break
                yield
        logging.info('GO')
        for _ in self._run(exp_win, ctl_win):
            if self.use_fmri:
                if fmri.get_ttl():
                    logging.exp(msg="fMRI TTL %d"%ttl_index)
                    ttl_index += 1
            yield

    def stop(self):
        pass

class Pause(Task):

    def __init__(self, **kwargs):
        if not 'name' in kwargs:
            kwargs['name'] = 'Pause'
            super().__init__(**kwargs)

    def _run(self, exp_win, ctl_win):
        text = """Taking a short break, relax..."""
        screen_text = visual.TextStim(
            exp_win, text=text,
            alignHoriz="center", color = 'white')

        while True:
            screen_text.draw(exp_win)
            screen_text.draw(ctl_win)
            yield
