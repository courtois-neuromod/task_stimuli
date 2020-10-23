import os, sys, time
from psychopy import visual, core, data, logging
from .task_base import Task

from ..shared import config

STIMULI_DURATION=3
BASELINE_BEGIN=5
BASELINE_END=5
ISI=4
RESPONSE_KEY='1'

class Things(Task):

    DEFAULT_INSTRUCTION = """You will see images on the screen.

Press the button when you see an unrecognizable object that was generated."""

    def __init__(self, design, images_path, run, *args,**kwargs):
        super().__init__(**kwargs)
        #TODO: image lists as params, subjects ....
        design = data.importConditions(design)
        self.design = [trial for trial in design if trial['run_nr'] == run]
        if os.path.exists(images_path) and os.path.exists(os.path.join(images_path, self.design[0]['image_path'])):
            self.images_path = images_path
        else:
            raise ValueError('Cannot find the listed images in %s '%images_path)

    def _setup(self, exp_win):

        self.fixation_cross = visual.ImageStim(
            exp_win,
            os.path.join('data','things','fixation_cross.png'),
            size=(.1,.1), units='height')

        self.trials = data.TrialHandler(self.design, 1, method='sequential')
        #preload all images
        for trial in self.trials:
            trial.stim = visual.ImageStim(
                exp_win,
                os.path.join(self.images_path, trial['image_path'])
                , size=(.1,.1), units='height')

    def _instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win, text=self.instruction,
            alignText="center", color = 'white', wrapWidth=config.WRAP_WIDTH)

        for frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield()

    def _run(self, exp_win, ctl_win):

        exp_win.logOnFlip(level=logging.EXP,msg='Things: task starting at %f'%time.time())
        for frameN in range(config.FRAME_RATE * BASELINE_BEGIN):
            self.fixation_cross.draw(exp_win)
            if ctl_win:
                self.fixation_cross.draw(ctl_win)
            yield frameN<2

        def set_trial_timing(trial, key):
            trial[key] = self.task_timer.getTime()

        for trial in self.trials:

            exp_win.logOnFlip(level=logging.EXP,msg='image: display %s'%trial['image_path'])
            exp_win.callOnFlip(set_trial_timing, trial, 'onset')
            for frameN in range(config.FRAME_RATE * trial['duration']):
                trial['stim'].draw(exp_win)
                self.fixation_cross.draw(exp_win)
                if ctl_win:
                    trial['stim'].draw(ctl_win)
                    self.fixation_cross.draw(ctl_win)
                yield()
            exp_win.callOnFlip(set_trial_timing, trial, 'offset')
            exp_win.logOnFlip(level=logging.EXP, msg='image: rest')
            for frameN in range(config.FRAME_RATE * ISI):
                yield()
            keypress = event.getKeys([RESPONSE_KEY])
            trial['response'] = len(keypress) > 0
            trial['response_time'] = trial['onset'] - keypress
            trial['duration'] = trial['offset']-trial['onset']

        for frameN in range(config.FRAME_RATE * BASELINE_END):
            self.fixation_cross.draw(exp_win)
            if ctl_win:
                self.fixation_cross.draw(ctl_win)
            yield frameN<2

    def save(self):
        self.trials.saveAsWideText(self._generate_tsv_filename())
