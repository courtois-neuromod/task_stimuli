import os, sys
from psychopy import visual, core, data, logging
from .task_base import Task

from ..shared import config

INSTRUCTION_DURATION=4
STIMULI_DURATION=4
BASELINE_BEGIN=5
BASELINE_END=5
ISI=4
IMAGES_FOLDER = '/home/basile/data/projects/task_stimuli/BOLD5000_Stimuli/Scene_Stimuli/Presented_Stimuli/ImageNet'

class Image(Task):

    def __init__(self,*args,**kwargs):
        super().__init__(**kwargs)
        #TODO: image lists as params, subjects ....
        self.image_names = data.importConditions('image_task/test_conditions.csv')

    def instructions(self, exp_win, ctl_win):
        instruction_text = """Please keep your eyes open an focused on the screen all the time.
You will see pictures of scenes and objects."""
        screen_text = visual.TextStim(
            exp_win, text=instruction_text,
            alignHoriz="center", color = 'white')

        for frameN in range(config.FRAME_RATE * INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            screen_text.draw(ctl_win)
            yield()

    def run(self, exp_win, ctl_win):

        trials = data.TrialHandler(self.image_names, 1, method='sequential')
        img = visual.ImageStim(exp_win,size=(1,1),units='height')
        for frameN in range(config.FRAME_RATE * BASELINE_BEGIN):
            yield()
        for trial in trials:
            image_path = os.path.join(IMAGES_FOLDER,trial['image_path'])
            img.image = image_path
            exp_win.logOnFlip(level=logging.EXP,msg='image: display %s'%image_path)
            for frameN in range(config.FRAME_RATE * STIMULI_DURATION):
                img.draw(exp_win)
                img.draw(ctl_win)
                yield()
            exp_win.logOnFlip(level=logging.EXP,msg='image: rest')
            for frameN in range(config.FRAME_RATE * ISI):
                yield()
        for frameN in range(config.FRAME_RATE * BASELINE_END):
            yield()
