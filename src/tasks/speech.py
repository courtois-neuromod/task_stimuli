import os, sys, time
from psychopy import visual, core, data, logging
from .task_base import Task

from ..shared import config

INSTRUCTION_DURATION=4
STIMULI_DURATION=4
BASELINE_BEGIN=5
BASELINE_END=5
ISI=4

class Speech(Task):

    def __init__(self, words_file,*args,**kwargs):
        super().__init__(**kwargs)
        if os.path.exists(words_file):
            self.words_file = words_file
            self.words_list = data.importConditions(self.words_file)
        else:
            raise ValueError('File %s does not exists'%words_file)

    def instructions(self, exp_win, ctl_win):
        instruction_text = """You will be presented text that you need to read out loud once it is presented to you."""
        screen_text = visual.TextStim(
            exp_win, text=instruction_text,
            alignHoriz="center", color = 'white')

        for frameN in range(config.FRAME_RATE * INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            screen_text.draw(ctl_win)
            yield()

    def _run(self, exp_win, ctl_win):

        self.trials = data.TrialHandler(self.words_list, 1, method='random')

        text = visual.TextStim(
            exp_win, text='',
            alignHoriz="center", color = 'white')

        exp_win.logOnFlip(level=logging.EXP,msg='speech: task starting at %f'%time.time())

        for frameN in range(config.FRAME_RATE * BASELINE_BEGIN):
            yield()
        for trial in self.trials:
            text.text = trial['text']
            exp_win.logOnFlip(level=logging.EXP,msg='speech: %s'%text.text)
            trial['onset'] = self.task_timer.getTime()
            for frameN in range(config.FRAME_RATE * STIMULI_DURATION):
                text.draw(exp_win)
                text.draw(ctl_win)
                yield()
            trial['offset'] = self.task_timer.getTime()
            trial['duration'] = trial['offset']-trial['onset']
            exp_win.logOnFlip(level=logging.EXP,msg='speech: rest')
            for frameN in range(config.FRAME_RATE * ISI):
                yield()
        for frameN in range(config.FRAME_RATE * BASELINE_END):
            yield()

    def save(self):
        self.trials.saveAsWideText(self._generate_tsv_filename())
