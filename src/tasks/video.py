import os, sys, time
#import pyglet
#pyglet.options['audio']=('pulse','directsound', 'openal', 'silent')

from psychopy import visual, core, data, logging
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

    def preload(self, exp_win):
        self.movie_stim = visual.MovieStim3(exp_win, self.filepath, units='pixels',autoLog=True)
        min_ratio = min(
            exp_win.size[0]/ self.movie_stim.size[0],
            exp_win.size[1]/ self.movie_stim.size[1])
        self.movie_stim.size = (
            min_ratio*self.movie_stim.size[0],
            min_ratio*self.movie_stim.size[1])
        print(self.movie_stim.size)
        print(self.movie_stim.duration)

    def _run(self, exp_win, ctl_win):
        # give the original size of the movie in pixels:
        #print(self.movie_stim.format.width, self.movie_stim.format.height)
        exp_win.logOnFlip(
            level=logging.EXP,
            msg='video: task starting at %f'%time.time())
        exp_win.setColor([-1,-1,-1])
        logging.info('PLAY')
        self.movie_stim.play()
        logging.info('PLAY2')
        while True:
            self.movie_stim.draw(exp_win)
            self.movie_stim.draw(ctl_win)
            logging.info('DRAW')

            yield
        exp_win.setColor([0,0,0])
        yield

    def stop(self):
        self.movie_stim.pause()
        #self.movie_stim.seek(0)
        self.movie_stim.win.setColor([0,0,0])
