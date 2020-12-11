import os, sys, time

from psychopy import visual, core, data, logging
from .task_base import Task

from ..shared import config

FADE_TO_GREY_DURATION = 2


class SingleVideo(Task):

    DEFAULT_INSTRUCTION = """You are about to watch a video.
Please keep your eyes open."""

    def __init__(self, filepath, *args, **kwargs):
        self._aspect_ratio = kwargs.pop("aspect_ratio", None)
        self._scaling = kwargs.pop("scaling", None)
        super().__init__(**kwargs)
        self.filepath = filepath
        if not os.path.exists(self.filepath):
            raise ValueError("File %s does not exists" % self.filepath)

    def _instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )

        for frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            grey = [
                -float(frameN) / config.FRAME_RATE / config.INSTRUCTION_DURATION
            ] * 3
            exp_win.setColor(grey)
            screen_text.draw(exp_win)
            if ctl_win:
                ctl_win.setColor(grey)
                screen_text.draw(ctl_win)
            yield True

    def _setup(self, exp_win):

        self.movie_stim = visual.MovieStim2(exp_win, self.filepath, units="pixels")
        # print(self.movie_stim._audioStream.__class__)
        aspect_ratio = (
            self._aspect_ratio or self.movie_stim.size[0] / self.movie_stim.size[1]
        )
        min_ratio = min(
            exp_win.size[0] / self.movie_stim.size[0],
            exp_win.size[1] / self.movie_stim.size[0] * aspect_ratio,
        )

        width = min_ratio * self.movie_stim.size[0]
        height = min_ratio * self.movie_stim.size[0] / aspect_ratio

        if self._scaling is not None:
            width *= self._scaling
            height *= self._scaling

        self.movie_stim.size = (width, height)
        self.duration = self.movie_stim.duration
        #        print(self.movie_stim.size)
        #        print(self.movie_stim.duration)
        super()._setup(exp_win)

    def _run(self, exp_win, ctl_win):
        # give the original size of the movie in pixels:
        # print(self.movie_stim.format.width, self.movie_stim.format.height)
        exp_win.logOnFlip(
            level=logging.EXP, msg="video: task starting at %f" % time.time()
        )
        self.movie_stim.play()
        while self.movie_stim.status != visual.FINISHED:
            self.movie_stim.draw(exp_win)
            if ctl_win:
                self.movie_stim.draw(ctl_win)
            yield False

    def _stop(self, exp_win, ctl_win):
        self.movie_stim.stop()
        for frameN in range(config.FRAME_RATE * FADE_TO_GREY_DURATION):
            grey = [float(frameN) / config.FRAME_RATE / FADE_TO_GREY_DURATION - 1] * 3
            exp_win.setColor(grey)
            if ctl_win:
                ctl_win.setColor(grey)
            yield True

    def _restart(self):
        self.movie_stim.setMovie(self.filepath)

    def unload(self):
        del self.movie_stim


class VideoAudioCheckLoop(SingleVideo):

    DEFAULT_INSTRUCTION = """We are setting up for the MRI session.
Make yourself comfortable.
We will play your personalized video so that you can ensure you can see the full screen and that the image is sharp."""

    def _setup(self, exp_win):
        super()._setup(exp_win)
        # set infinite loop for setup, need to be skipped
        self.movie_stim.loop = -1
        self.use_fmri = False
        self.use_eyetracking = False
