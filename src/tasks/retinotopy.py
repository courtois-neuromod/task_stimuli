import os, sys, time, random
from psychopy import visual, core, data, logging, event
from .task_base import Task
import numpy as np
from colorama import Fore
import pandas

from ..shared import config, utils


def generate_wedge():
    pass

class Retinotopy(Task):

    DEFAULT_INSTRUCTION = """You will see a dot in the center of the screen.
    Fixate that dot, and press the <A> button when the color changes.
    Moving patterns will be shown in the meantime, but you need to pay attention to the dot!"""


    DOT_COLORS = [(237, 96, 31), (66, 135, 245)]
    DOT_MIN_DURATION = 3
    RESPONSE_KEY = 'a'

    def __init__(self, condition, *args, **kwargs):
        super().__init__(**kwargs)
        if condition not in ['RETCCW', 'RETCW', 'RETEXP', 'RETCON', 'RETBAR']:
            raise ValueError("Condition {condition} does not exists")
        self.condition = condition


    def _setup(self, exp_win):
        self.fixation_dot = visual.Circle(
            exp_win,
            size=.15,
            units='deg',
            opacity=.8,
            color=self.DOT_COLORS[0],
            colorSpace='rgb255'
        )

        self.img = visual.ImageStim(
            exp_win,
            size=(768,768),
            units='pixels',
            flipVert=True)

        self._images = np.load('data/retinotopy/images.npz')['images'].astype(np.float32)/255.
        if 'CW' in self.condition:
            aperture_file = 'apertures_wedge_newtr.npz'
        elif self.condition in ['RETEXP', 'RETCON']:
            aperture_file = '/apertures_ring.npz'
        elif self.condition == 'RETBAR':
            aperture_file =  'apertures_bars.npz'
        self._apertures = np.load(f"data/retinotopy/{aperture_file}")['apertures'].astype(np.float32)/128.-1

        # draw random order with different successive stimuli
        self._images_random = np.random.randint(0, 99, size=(8*32*15)) #max nframe in CW conditions
        while any(np.ediff1d(self._images_random, to_begin=[-1])==0):
            self._images_random[np.ediff1d(self._images_random, to_begin=[-1])==0] += 1
            self._images_random[self._images_random==100] = 0


        self.duration = 300 # seconds
        self._progress_bar_refresh_rate = 15


        self.events = pandas.DataFrame()
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
            yield frameN < 2
        yield True

    def _run(self, exp_win, ctl_win):
        event.getKeys() # flush all keypresses
        exp_win.logOnFlip(
            level=logging.EXP, msg=f"Retinotopy {self.condition}: task starting at {time.time()}"
        )

        color_state = 0
        dot_next_change = 0
        dot_change_idx = 0

        for do_yield in self._run_condition(exp_win, ctl_win):
            #TODO: log responses
            keypresses = event.getKeys(self.RESPONSE_KEY, timeStamped=self.task_timer)
            for k in keypresses:
                rt = k[1] - dot_last_change
                self._log_event({
                    'trial_type':'response',
                    'trial_number': dot_change_idx,
                    'response_time': rt
                })


            if self.task_timer.getTime() > dot_next_change:
                color_state = (color_state+1)%2
                self.fixation_dot.setColor(
                    self.DOT_COLORS[color_state],
                    colorSpace='rgb255')
                dot_last_change = dot_next_change
                dot_next_change += self.DOT_MIN_DURATION + random.random()*5
                exp_win.callOnFlip(
                    self._log_event,
                    {'trial_type':'dot_color',
                    'trial_number': dot_change_idx,
                    'color': color_state},
                    clock='flip'
                )
                dot_change_idx += 1
                do_yield = True
            self.fixation_dot.draw(exp_win)
            if ctl_win:
                self.fixation_dot.draw(exp_win)
            if do_yield:
                yield True


    def _run_condition(self, exp_win, ctl_win):

        frame_duration = 1/15.

        initial_wait = 16 if self.condition == 'RETBAR' else 22
        initial_wait = 2 if self.condition == 'RETBAR' else 4
        middle_blank = 0
        cycle_length = 21*config.TR # 31.29, a bit shorter than 32s
        yield True
        # wait until it's almost time to render first frame
        yield from utils.wait_until_yield(
            self.task_timer,
            initial_wait - .2,
            keyboard_accuracy=.001,
            hogCPUperiod=2/config.FRAME_RATE)

        if 'BAR' in self.condition:
            middle_blank = 12
            conds = np.asarray([0,1,0,1,2,3,2,3])
            for ci, start_idx in enumerate(conds*28*15):
                order = 1-(ci%4>1)*2
                for fi, frame in enumerate(range(28*15)[::order]):
                    flip_time = (initial_wait + (ci>3) * middle_blank +
                        (ci*cycle_length*15+fi) * frame_duration
                        - 1/config.FRAME_RATE)

                    #flipVert = 1 - 2*(ci in [3,6,7])
                    #flipHoriz = 1 - 2*(ci in [2])
                    image_idx = self._images_random[ci*32*15+fi]
                    self.img.image = self._images[..., image_idx]
                    self.img.mask = self._apertures[..., start_idx+frame]

                    yield from utils.wait_until_yield(
                        self.task_timer,
                        flip_time,
                        keyboard_accuracy=.001,
                        hogCPUperiod=2/config.FRAME_RATE)

                    self.img.draw(exp_win)
                    if ctl_win:
                        self.img.draw(ctl_win)

                    exp_win.callOnFlip(
                        self._log_event,
                        {'condition': self.condition, 'image_idx': image_idx, 'aperture': frame},
                        clock='flip'
                    )
                    yield True
                print(self.task_timer.getTime(),flip_time)
                yield True
        else:
            order = -1 if self.condition in ['RETCW', 'RETCON'] else 1
            for ci in range(2): # 8 cycles
                display_length = cycle_length if 'CW' in self.condition else 28 # shorten next loop, adds 4s blank
                for fi, frame in enumerate(range(int(display_length*15))[::order]): # 32/28 sec at 15Hz
                    flip_time = initial_wait + (ci*cycle_length*15+fi) * frame_duration - 1/config.FRAME_RATE
                    image_idx = self._images_random[ci*32*15+fi]
                    self.img.image = self._images[..., image_idx]
                    self.img.mask = self._apertures[..., frame]

                    yield from utils.wait_until_yield(
                        self.task_timer,
                        flip_time,
                        keyboard_accuracy=.001,
                        hogCPUperiod=2/config.FRAME_RATE)

                    self.img.draw(exp_win)
                    if ctl_win:
                        self.img.draw(ctl_win)

                    exp_win.callOnFlip(
                        self._log_event,
                        {'condition': self.condition, 'image_idx': image_idx, 'aperture': frame},
                        clock='flip'
                    )
                    yield True

                if 'CW' not in self.condition:
                    yield True # blank
        yield True

        yield from utils.wait_until_yield(
            self.task_timer,
            initial_wait * 2 + ((ci+1)*cycle_length*15+fi) * frame_duration + middle_blank,
            keyboard_accuracy=.001)

    def unload(self):
        del self._apertures, self._images
        del self.img, self._images_random, self.fixation_dot
