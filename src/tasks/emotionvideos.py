from calendar import c
import os, sys, time
from psychopy import visual, core, data, logging, event
from .task_base import Task
import numpy as np
from colorama import Fore
import pandas as pd

from ..shared import config, utils, eyetracking

FADE_TO_GREY_DURATION = 2
SCALING_EMOTION_VIDEOS = 600 #pix

class EmotionVideos(Task):

    DEFAULT_INSTRUCTION = """You will see short videos on screen.
    Please keep your eyes open, and fixate the dot at the beginning of each segment."""

    def __init__(self, design, videos_path, run, target_duration, **kwargs):
        self.run_id = run
        self.n_trial = 0
        self.path_design = design
        self.target_duration = target_duration
        self.design = pd.read_csv(design, sep='\t')
        self._task_completed = False
        if os.path.exists(videos_path):
            self.videos_path = videos_path
        else:
            raise ValueError("Cannot find the videos in %s " % videos_path)

        super().__init__(**kwargs)


    def _setup(self, exp_win):

        super()._setup(exp_win)

        """
        #If fixation is a cross
        self.fixation_image = visual.ImageStim(
            exp_win,
            os.path.join("data", "emotionvideos", "fixations", "fixation_cross.png"),
            size=15,
            units='deg',
        )
        """

        #If fixation is a bull's eye instead of a fixation cross
        """
        self.fixation_image = visual.ImageStim(
            exp_win,
            os.path.join("data", "emotionvideos", "fixations", "fixation.png"),
            size=(40,40),
            units='pix',
        )"""
        self.fixation = eyetracking.fixation_dot(exp_win)

        #Preload all videos
        self._stimuli = []
        for idx, trial in enumerate(self.design.Gif):
            self.n_trial = idx
            video = visual.MovieStim(
                exp_win, os.path.join(self.videos_path, trial),
                units = 'pix',
            )
            width_video, height_video = video.videoSize
            #Rescale videos if needed
            if width_video >= height_video:
                scaling = SCALING_EMOTION_VIDEOS / width_video
            else:
                scaling = SCALING_EMOTION_VIDEOS / height_video
            if scaling < SCALING_EMOTION_VIDEOS:
                video.size = (width_video * scaling, height_video * scaling)
            self._stimuli.append(video)

        self.trials = data.TrialHandler(self.path_design, 1, method="sequential")
        self.duration = len(self.design)
        self._progress_bar_refresh_rate = 0  # 2 flips per trial
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
            yield


    def _run(self, exp_win, ctl_win):
        exp_win.colorSpace='rgb255'
        exp_win.color = [54,69,79]

        exp_win.logOnFlip(
            level = logging.EXP, msg = "EmotionVideos: task starting at %f" % time.time()
        )
        yield True
        yield True

        for trial_n, (trial, stimuli) in enumerate(zip(self.trials, self._stimuli)):
            self.n_trial = trial_n

            exp_win.logOnFlip(
                level = logging.EXP,
                msg = f"videos: {trial['Gif']}",
            )
            self.progress_bar.set_description(
                f"Trial {trial_n}: {trial['Gif']}"
            )
            self.progress_bar.update(1)

            #Draw to backbuffer
            for stim in self.fixation:
                stim.draw(exp_win)
                if ctl_win:
                    stim.draw(ctl_win)
            #Wait onset for fixation
            utils.wait_until(self.task_timer, trial["onset_fixation"] - 1 / config.FRAME_RATE)
            yield True #flip
            trial['onset_fixation_flip'] = self._exp_win_last_flip_time - self._exp_win_first_flip_time

            #Wait onset for videos
            utils.wait_until(self.task_timer, trial["onset"] - 1 / config.FRAME_RATE)
            if stimuli.pts != 0:
                stimuli.replay()
            else:
                stimuli.play()
            # separate draw to log precise flip start
            stimuli.draw()
            yield True
            trial['onset_video_flip'] = self._exp_win_last_flip_time - self._exp_win_first_flip_time
            while stimuli.status != visual.FINISHED:
                stimuli.draw()
                yield False #flip without clearing buffer for perfs
            # clear screen and back buffer
            yield True
            yield True
            stimuli._player.unload() #stop+cleanup

        utils.wait_until(self.task_timer, self.target_duration)
        self._task_completed = True


    def _restart(self):
        self.trials = data.TrialHandler(self.path_design, 1, method="sequential")

    def _stop(self, exp_win, ctl_win):
        for frameN in range(config.FRAME_RATE * FADE_TO_GREY_DURATION):
            grey = [float(frameN) / config.FRAME_RATE / FADE_TO_GREY_DURATION - 1] * 3
            exp_win.setColor(grey, colorSpace='rgb')
            if ctl_win:
                ctl_win.setColor(grey)
            yield True

    def _save(self):
        self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))

    def unload(self):
        del self._stimuli
