import os
from psychopy import logging, visual, core, event

from ..shared import fmri, config

class Task(object):

    DEFAULT_INSTRUCTION=''

    def __init__(self, name, instruction=None):
        self.name = name
        self.use_eyetracking = False
        if instruction is None:
            self.instruction = self.__class__.DEFAULT_INSTRUCTION
        else:
            self.instruction = instruction

    # setup large files for accurate start with other recordings (scanner, biopac...)
    def setup(self, exp_win, output_path, output_fname_base, use_fmri=False, use_eyetracking=False):
        self.output_path = output_path
        self.output_fname_base = output_fname_base
        self.use_fmri = use_fmri
        self.use_eyetracking = use_eyetracking
        self._setup(exp_win)

    def _setup(self, exp_win):
        pass

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
                yield True
        fmri.get_ttl() # flush any remaining TTL keys
        if self.use_fmri:
            ttl_index = 0
            logging.exp(msg="waiting for fMRI TTL")
            while True:
                if fmri.get_ttl():
                    #TODO: log real timing of TTL?
                    logging.exp(msg="fMRI TTL %d"%ttl_index)
                    ttl_index += 1
                    break
                yield False # no need to draw
        logging.info('GO')
        self.task_timer = core.Clock()
        for _ in self._run(exp_win, ctl_win):
            if self.use_fmri:
                if fmri.get_ttl():
                    logging.exp(msg="fMRI TTL %d"%ttl_index)
                    ttl_index += 1
            yield True

    def stop(self):
        pass

    def restart(self):
        if hasattr(self, '_restart'):
            self._restart()

    def save(self):
        pass

class Pause(Task):

    def __init__(self, text="Taking a short break, relax...", **kwargs):
        self.wait_key = kwargs.pop('wait_key', False)
        if not 'name' in kwargs:
            kwargs['name'] = 'Pause'
        super().__init__(**kwargs)
        self.text = text

    def _setup(self, exp_win):
        self.use_fmri = False
        self.use_eyetracking = False

    def _run(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win, text=self.text,
            alignHoriz="center", color = 'white',wrapWidth=config.WRAP_WIDTH)

        while True:
            if not self.wait_key is False:
                if len(event.getKeys(self.wait_key)):
                    break
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield


class Fixation(Task):

    DEFAULT_INSTRUCTION = """We are going to acquired resting-state data.
Please keep your eyes open and fixate the cross.
Do not think about something in particular, let your mind wander..."""

    def __init__(self, duration=7*60, symbol="+", **kwargs):
        if not 'name' in kwargs:
            kwargs['name'] = 'Pause'
        super().__init__(**kwargs)
        self.duration = duration
        self.symbol = symbol

    def instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win, text=self.instruction,
            alignHoriz="center", color = 'white', wrapWidth=config.WRAP_WIDTH)

        for frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield

    def _run(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win, text=self.symbol,
            alignHoriz="center", color = 'white')
        screen_text.height = .2

        for frameN in range(config.FRAME_RATE * self.duration):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield
