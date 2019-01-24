import os
from psychopy import logging, visual, core

from ..shared import fmri

class Task(object):

    def __init__(self, name, use_fmri=False, use_eyetracking=False):
        self.name = name
        self.use_fmri = use_fmri
        self.use_eyetracking = use_eyetracking

    # setup large files for accurate start with other recordings (scanner, biopac...)
    def setup(self, exp_win, output_path, output_fname_base):
        self.output_path = output_path
        self.output_fname_base = output_fname_base

    def _generate_tsv_filename(self):
        for fi in range(1000):
            fname = os.path.join(self.output_path, '%s_%s_%03d.tsv'%(self.output_fname_base, self.name,fi))
            if not os.path.exists(fname):
                break
        return fname

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
        self.task_timer = core.Clock()
        for _ in self._run(exp_win, ctl_win):
            if self.use_fmri:
                if fmri.get_ttl():
                    logging.exp(msg="fMRI TTL %d"%ttl_index)
                    ttl_index += 1
            yield

    def stop(self):
        pass

    def save(self):
        pass

class Pause(Task):

    def __init__(self, text="Taking a short break, relax...", **kwargs):
        if not 'name' in kwargs:
            kwargs['name'] = 'Pause'
        super().__init__(**kwargs)
        self.text = text

    def _run(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win, text=self.text,
            alignHoriz="center", color = 'white',wrapWidth=1.6)

        while True:
            screen_text.draw(exp_win)
            screen_text.draw(ctl_win)
            yield
