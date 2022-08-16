from calendar import c
import os, sys, time
from psychopy import visual, core, data, logging, event
from .task_base import Task
import numpy as np
from colorama import Fore

from ..shared import config, utils

FADE_TO_GREY_DURATION = 2
SCALING_EMOTION_VIDEOS = 600 #pix

class EmotionVideos(Task):

    DEFAULT_INSTRUCTION = """You will see short videos on screen. 
    Please keep your eyes open, and fixate the cross at the beginning of each segment."""

    def __init__(self, design, videos_path, run, *args, **kwargs):
        self.run_id = run
        self.design = design
        self._task_completed = False
        if os.path.exists(videos_path):
            self.videos_path = videos_path
        else:
            raise ValueError("Cannot find the videos in %s " % videos_path)

        super().__init__(**kwargs)


    def _setup(self, exp_win):
        super()._setup(exp_win)

        """
        If fixation is a cross
        self.fixation_cross = visual.ImageStim(
            exp_win,
            os.path.join("data", "emotionvideos", "pngs", "fixation_cross.png"),
            size=2,
            units='deg',
        )
        """
        #If fixation is a bull's eye instead of a fixation cross
        try:
            self.fixation_image = visual.ImageStim(
                exp_win,
                os.path.join("data", "emotionvideos", "pngs", "fixframe_" + str(exp_win.size[0]) + "_" + str(exp_win.size[1]) + ".jpg"),
                size=(exp_win.size[0], exp_win.size[1]),
                units='pix',
            )
        except:
            self.fixation_image = visual.ImageStim(
                exp_win,
                os.path.join("data", "emotionvideos", "pngs", "fixframe.jpg"),
                size=(exp_win.size[1]*(1280/1024), exp_win.size[1]),
                #size=(1280, 1024),
                units='pix',
            )
        
        #Preload all videos
        self._stimuli = []
        for trial in self.design.Gif:
            video = visual.MovieStim(
                exp_win, os.path.join(self.videos_path, trial),
                units = 'pix',
            )
            width_video, height_video = video.size[0], video.size[1]
            #Rescale videos if needed
            if width_video >= height_video:
                scaling = SCALING_EMOTION_VIDEOS / width_video
            else:
                scaling = SCALING_EMOTION_VIDEOS / height_video
            if scaling < SCALING_EMOTION_VIDEOS:
                video.size = (width_video * scaling, height_video * scaling)
            self._stimuli.append(video)

        self.trials = data.TrialHandler(self.design, 1, method="sequential")
        self.duration = len(self.design)
        self._progress_bar_refresh_rate = 2  # 2 flips per trial
        super()._setup(exp_win)


    def _instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )

        for frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield ()


    def _run(self, exp_win, ctl_win):
        exp_win.logOnFlip(
            level = logging.EXP, msg = "EmotionVideos: task starting at %f" % time.time()
        )
        
        for trial_n, (trial, stimuli) in enumerate(zip(self.trials, self._stimuli)):
            exp_win.logOnFlip(
                level = logging.EXP,
                msg = f"videos: {trial['videos_path']}",
            )
            self.progress_bar.set_description(
                f"Trial {trial_n}: {trial['videos_path']}"
            )

            #Draw to backbuffer
            self.fixation_cross.draw(exp_win)
            if ctl_win:
                self.fixation_cross.draw(ctl_win)
            #Wait onset
            utils.wait_until(self.task_timer, trial["onset"] - 1 / config.FRAME_RATE)
            while stimuli.status != visual.FINISHED:
                stimuli.draw()
                yield True #flip

        self._task_completed = True


    def _stop(self, n_trial, exp_win, ctl_win):
        self._stimuli[n_trial].stop()
        for frameN in range(config.FRAME_RATE * FADE_TO_GREY_DURATION):
            grey = [float(frameN) / config.FRAME_RATE / FADE_TO_GREY_DURATION - 1] * 3
            exp_win.setColor(grey, colorSpace='rgb')
            if ctl_win:
                ctl_win.setColor(grey)
            yield True


    def unload(self):
        del self._stimuli