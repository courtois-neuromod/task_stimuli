import os, sys, time
from psychopy import visual, core, data, logging, event

from .task_base import Task
from .videogame import _onPygletKeyPress, _onPygletKeyRelease, _keyPressBuffer, _keyReleaseBuffer
from ..shared import config, utils

class ButtonPressTask(Task):

    BUTTONS = {
        'l': [(132,176),(175,176),(196,200),(175,222),(132,222)],
        'r': [(250,176),(290,176),(290,222),(250,222),(230,200)],
        'u': [(189,162),(189,120),(233,120),(233,162),(211,184)],
        'd': [(189,235),(189,276),(232,276),(232,235),(211,215)],
        'a': [(648, 200), 25],
        'b': [(592, 253), 25],
        'x': [(592, 144), 25],
        'y': [(538, 200), 25],
    }

    FINAL_WAIT = 9

    DEFAULT_INSTRUCTION = """You will be instructed to press the buttons of the controller for short or long durations."""

    def __init__(self, design, run, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.design = data.importConditions(design)
        self.run_id = run
        self.duration = len(self.design)
        self._progress_bar_refresh_rate = 3 # 3 flips per trial

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
        if self.run_id == 1:
            yield True
            yield from self._long_instructions(exp_win, ctl_win)

    def _long_instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win,
            text="""The long bar indicates long keypresses blocks,
you need to time the press and the release to the button that light-up""",
            alignText="center",
            color="white",
            pos=(0,-.75),
            wrapWidth=config.WRAP_WIDTH,
        )
        self._controller_img.draw(exp_win)
        screen_text.draw(exp_win)
        self._cue['long'].draw(exp_win)
        yield True
        core.wait(config.INSTRUCTION_DURATION)

        screen_text.text = """The dot indicates short keypresses,
You have to press and release immediately the button that light-up."""
        self._controller_img.draw(exp_win)
        screen_text.draw(exp_win)
        self._cue['short'].draw(exp_win)
        yield True
        core.wait(config.INSTRUCTION_DURATION)
        yield True


    def _setup(self, exp_win):

        self.trials = data.TrialHandler(self.design, 1, method="sequential")

        self._controller_img = visual.ImageStim(
            exp_win,
            image="data/game_ctrlr/ctrlr.png",
            size=(800, 481),
            units="pixels"
        )

        self._cue = {
            'short': visual.Circle(
                exp_win, pos=[0,0], radius=25, units="pixels",
                lineColor=(255,165,30), fillColor=(255,165,30), colorSpace='rgb255',),
            'long': visual.Rect(
                exp_win, width=100., height=20, units="pixels",
                fillColor=(40,220,120), colorSpace='rgb255',),
            }

        buttons_aspect = {
            'fillColor':(255,160,110),
            'colorSpace':'rgb255',
            'opacity':.6,
            'lineWidth':0
            }

        self._buttons = {
            key: (
                visual.ShapeStim(
                    exp_win,
                    vertices=[(s - self._controller_img.size/2) * (1,-1) for s in shape],
                    units="pixels",
                    **buttons_aspect)
                if len(shape)>2
                else visual.Circle(
                    exp_win,
                    radius=shape[1],
                    pos=(shape[0] - self._controller_img.size/2) * (1,-1),
                    units="pixels",
                    **buttons_aspect))
                for key, shape in self.BUTTONS.items()
                }

    def _set_key_handler(self, exp_win):
        # activate repeat keys
        exp_win.winHandle.on_key_press = _onPygletKeyPress
        exp_win.winHandle.on_key_release = _onPygletKeyRelease
        self.pressed_keys = set()

    def _unset_key_handler(self, exp_win):
        # deactivate custom keys handling
        exp_win.winHandle.on_key_press = event._onPygletKey
        # del exp_win.winHandle.on_key_release

    def _handle_controller_presses(self, exp_win):
        exp_win.winHandle.dispatch_events()
        global _keyPressBuffer, _keyReleaseBuffer

        time_offset = core.getTime() - self.task_timer.getTime()

        key_presses = [(k, t-time_offset) for (k,t) in _keyPressBuffer]
        key_releases = [(k, t-time_offset) for (k,t) in _keyReleaseBuffer]

        _keyReleaseBuffer.clear()
        _keyPressBuffer.clear()

        return key_presses, key_releases

    def _run(self, exp_win, ctl_win):

        self._set_key_handler(exp_win)

        time_offset = core.getTime() - self.task_timer.getTime()

        for trial_n, trial in enumerate(self.trials):

            # draw cue, flip
            self._controller_img.draw(exp_win)
            self._cue[trial['condition']].draw(exp_win)
            yield True

            exp_win.logOnFlip(
                level=logging.EXP,
                msg=f"image: {trial['condition']}",
            )

            # draw to backbuffer
            self._controller_img.draw(exp_win)
            self._cue[trial['condition']].draw(exp_win)
            self._buttons[trial['key']].draw(exp_win)

            utils.wait_until(self.task_timer, trial["onset"] - 1 / config.FRAME_RATE)
#            keypresses = event.getKeys(self.RESPONSE_KEYS) # flush response keys
            yield True  # flip
            trial["onset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )
            self.progress_bar.set_description(
                f"Trial {trial_n}:: {trial['condition']} {trial['key']}"
            )


            # reset
            self._controller_img.draw(exp_win)
            self._cue[trial['condition']].draw(exp_win)

            utils.wait_until(self.task_timer, trial["onset"] + trial["duration"] - 1 / config.FRAME_RATE)
            yield True  # flip
            trial["offset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )

            utils.wait_until(self.task_timer, trial["offset_flip"] + 1 )
            key_pressed, key_released = self._handle_controller_presses(exp_win)
            for k in ['key_press_time', 'key_press_rt', 'key_release_time', 'key_release_rt', 'key_duration', 'all_keypresses', 'all_key_releases']:
                trial[k] = None

            kp_matches = [(k,t) for k,t in key_pressed if k==trial['key']]
            kr_matches = [(k,t) for k,t in key_released if k==trial['key']]

            if len(kp_matches):
                trial['key_press_time'] = kp_matches[0][1]
                trial['key_press_rt'] = trial['key_press_time']  - trial['onset_flip']
            if len(kr_matches):
                trial['key_release_time'] = kr_matches[0][1]
                if len(kp_matches):
                    trial['key_duration'] = trial['key_release_time'] - trial['key_press_time']
                # only pertinent for long keypresses, but still computing it for short ones
                trial['key_release_rt'] = trial['key_release_time']  - trial['offset_flip']
            trial['all_keypresses'] = key_pressed # log to exclude trial with confounded keys
            trial['all_keyreleases'] = key_released
            self.progress_bar.set_description(
                f"Trial {trial_n}:: {trial['condition']} {trial['key']} rt={trial.get('key_press_rt')}"
            )
        utils.wait_until(self.task_timer, trial["onset"] + trial['duration'] + self.FINAL_WAIT)
        self._unset_key_handler(exp_win)

    def _stop(self, exp_win, ctl_win):
        self._unset_key_handler(exp_win)
        yield

    def _restart(self):
        self.trials = data.TrialHandler(self.design, 1, method="sequential")

    def _save(self):
        self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
        return False
