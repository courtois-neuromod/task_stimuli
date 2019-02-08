import os, sys, time

from psychopy import visual, core, data, logging
from .task_base import Task

from ..shared import config



class SingleVideo(Task):

    DEFAULT_INSTRUCTION = """You are about to watch a video.
Please keep your eyes open."""

    def __init__(self, filepath, *args,**kwargs):
        super().__init__(**kwargs)
        #TODO: image lists as params, subjects ....
        self.filepath = filepath
        if not os.path.exists(self.filepath):
            raise ValueError('File %s does not exists'%self.filepath)

    def instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win, text=self.instruction,
            alignHoriz="center", color = 'white', wrapWidth=config.WRAP_WIDTH)

        for frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            screen_text.draw(ctl_win)
            yield

    def _setup(self, exp_win):

        self.movie_stim = visual.MovieStim3(exp_win, self.filepath, units='pixels')
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
        self.movie_stim.play()
        while self.movie_stim.status != visual.FINISHED:
            self.movie_stim.draw(exp_win)
            self.movie_stim.draw(ctl_win)

            yield
        exp_win.setColor([0,0,0])
        yield

    def stop(self):
        self.movie_stim.pause()
        self.movie_stim.seek(0)
        self.movie_stim.win.setColor([0,0,0])


class VideoAudioCheckLoop(SingleVideo):

    DEFAULT_INSTRUCTION = """We are setting up for the MRI session.
Make yourself comfortable.
We will play you personalized video so that you can ensure that you can see the full screen and that the image is sharp."""


    def _setup(self, exp_win):
        super()._setup(exp_win)
        # set infinite loop for setup, need to be skipped
        self.movie_stim.loop = -1
        self.use_fmri = False
        self.use_eyetracking = False
