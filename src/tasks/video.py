import os, sys, time

import psychopy
psychopy.prefs.hardware['audioLib'] = ['PTB', 'sounddevice', 'pyo','pygame']
from psychopy import visual, core, data, logging
from .task_base import Task

from ..shared import config

FADE_TO_GREY_DURATION = 2


class SingleVideo(Task):

    DEFAULT_INSTRUCTION = """You are about to watch a video.
Please keep your eyes open,
and fixate the dot at the beginning and end of the segment."""

    FIXTASK_INSTRUCTION = """You are about to watch a video.
Please keep your eyes open,
and fixate the dot whenever it appears in the segment."""

    def __init__(self, filepath, *args, **kwargs):
        self._aspect_ratio = kwargs.pop("aspect_ratio", None)
        self._scaling = kwargs.pop("scaling", None)
        self._endstart_fixduration = kwargs.pop("endstart_fixduration", 0)
        self._inmovie_fixations = kwargs.pop("inmovie_fixations", False)
        self._infix_freq = kwargs.pop("infix_freq", 20)
        self._infix_dur = kwargs.pop("infix_dur", 1.5)
        instruct = self.__class__.FIXTASK_INSTRUCTION if self._inmovie_fixations else self.__class__.DEFAULT_INSTRUCTION
        super().__init__(instruction=instruct, **kwargs)
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
            exp_win.setColor(grey, colorSpace='rgb')
            screen_text.draw(exp_win)
            if ctl_win:
                ctl_win.setColor(grey)
                screen_text.draw(ctl_win)
            yield True

    def _setup(self, exp_win):

        if self._endstart_fixduration > 0 or self._inmovie_fixations:
            from ..shared.eyetracking import fixation_dot
            self.fixation_dot = fixation_dot(exp_win)

        if self._inmovie_fixations:
            self.grey_bgd = visual.Rect(exp_win, size=exp_win.size, lineWidth=0,
                                        colorSpace='rgb', fillColor=(-.58, -.58, -.58)) # (54, 54, 54) on 0-255 scale
            self.black_bgd = visual.Rect(exp_win, size=exp_win.size, lineWidth=0,
                                        colorSpace='rgb', fillColor=(-1, -1, -1))

        self.movie_stim = visual.MovieStim2(exp_win, self.filepath, units="pix")
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
        fixation_on = False
        self.movie_stim.play()
        while self.movie_stim.status != visual.FINISHED:
            #self.black_bgd.draw(exp_win)
            self.movie_stim.draw(exp_win)
            next_frame_time = self.movie_stim.getCurrentFrameTime()

            if ctl_win:
                self.movie_stim.draw(ctl_win)
            if self._endstart_fixduration > 0:
                if next_frame_time <= self._endstart_fixduration or \
                    next_frame_time >= self.movie_stim.duration-self._endstart_fixduration:
                    for stim in self.fixation_dot:
                        stim.draw(exp_win)
            elif self._inmovie_fixations:
                if (next_frame_time % self._infix_freq < self._infix_dur):
                    self.black_bgd.draw(exp_win)
                    #self.grey_bgd.draw(exp_win)
                    for stim in self.fixation_dot:
                        stim.draw(exp_win)
                    if not fixation_on:
                        exp_win.logOnFlip(
                            level=logging.EXP, msg="fixation onset at %f" % time.time()
                        )
                        fixation_on = True
                elif fixation_on:
                    exp_win.logOnFlip(
                        level=logging.EXP, msg="fixation offset at %f" % time.time()
                    )
                    fixation_on = False

            '''
            if self._endstart_fixduration > 0 or self._inmovie_fixations:
                next_frame_time = self.movie_stim.getCurrentFrameTime()
                if next_frame_time <= self._endstart_fixduration or \
                    next_frame_time >= self.movie_stim.duration-self._endstart_fixduration:
                    for stim in self.fixation_dot:
                        stim.draw(exp_win)
                    if not fixation_on:
                        exp_win.logOnFlip(
                            level=logging.EXP, msg="fixation onset at %s" % next_frame_time
                        )
                        fixation_on = True
                elif self._inmovie_fixations and (next_frame_time % self._infix_freq < self._infix_dur):
                    self.black_bgd.draw(exp_win)
                    #self.grey_bgd.draw(exp_win)
                    for stim in self.fixation_dot:
                        stim.draw(exp_win)
                    if not fixation_on:
                        exp_win.logOnFlip(
                            level=logging.EXP, msg="fixation onset at %s" % next_frame_time
                        )
                        fixation_on = True
                elif fixation_on:
                    exp_win.logOnFlip(
                        level=logging.EXP, msg="fixation offset at %s" % next_frame_time
                    )
                    fixation_on = False
            '''
            yield False

    def _stop(self, exp_win, ctl_win):
        self.movie_stim.stop()
        for frameN in range(config.FRAME_RATE * FADE_TO_GREY_DURATION):
            grey = [float(frameN) / config.FRAME_RATE / FADE_TO_GREY_DURATION - 1] * 3
            exp_win.setColor(grey, colorSpace='rgb')
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
