import os, sys
#import pyglet
#pyglet.options['audio']=('pulse','directsound', 'openal', 'silent')

from psychopy import visual, core, data
from .task_base import Task

from ..shared import config

INSTRUCTION_DURATION = 1

class SingleVideo(Task):

    def __init__(self, filepath, *args,**kwargs):
        super().__init__(**kwargs)
        #TODO: image lists as params, subjects ....
        self.filepath = filepath


    def instructions(self, exp_win, ctl_win):
        instruction_text = """You are about to watch a video. Please keep your eyes opened."""
        screen_text = visual.TextStim(
            exp_win, text=instruction_text,
            alignHoriz="center", color = 'white')

        for frameN in range(config.FRAME_RATE * INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            screen_text.draw(ctl_win)
            yield

    def run(self, exp_win, ctl_win):
        self.movie_stim = visual.MovieStim3(exp_win, self.filepath, size=exp_win.size, units='pixels')
        print(self.movie_stim.duration)
        # give the original size of the movie in pixels:
        #print(self.movie_stim.format.width, self.movie_stim.format.height)
        exp_win.logOnFlip(level=logging.EXP,msg='video: task starting at %f'%time.time())
        while True:
            self.movie_stim.draw(exp_win)
            self.movie_stim.draw(ctl_win)
            yield
