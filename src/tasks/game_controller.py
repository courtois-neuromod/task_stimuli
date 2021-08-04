import os, sys, time
from psychopy import visual, core, data, logging, event
from .task_base import Task
from .videogames import _onPygletKeyPress, _onPygletKeyRelease

class ButtonPressTask(Task):

    BUTTONS = {
        'L': [(396,522),(510,522),(568,582),(510,645),(396,645)],
#        'R': [(396,522),(510,522),(568,582),(510,645),(396,645)],

    }


    DEFAULT_INSTRUCTION = """You will be instructed to press the buttons of the controller.
You will either have to do short presses or hold press until the signal disappears.
Short presses are instructed by a dot in the center and long-presses by a bar"""

    def __init__(self, design, run, *args, **kwargs):
        super().__init__(*args, **kwargs)
        design = data.importConditions(design)
        self.run_id = run
        self.design = [trial for trial in design if trial["run"] == run]

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

    def _setup(self, exp_win):

        self._controller_img = visual.ImageStim(
            exp_win,
            image="data/game_ctrlr/ctrlr.png",
            size=10,
            units='deg'
        )

        self._cue = {
            'short': visual.Circle(pos=[0,0], radius=5),
            'long': visual.Line(start=[-20,0], end=[20, 0], lineWidth=5),
            }

        self._buttons = {
            key: (visual.ShapeStim(exp_win, vertices=shape)
                if len(shape)>2
                else visual.Circle(exp_win, radius=shape[1], pos=shape=[0]))
                for key, shape in self.BUTTONS.items()}

    def _set_key_handler(self, exp_win):
        # activate repeat keys
        exp_win.winHandle.on_key_press = _onPygletKeyPress
        exp_win.winHandle.on_key_release = _onPygletKeyRelease
        self.pressed_keys = set()

    def _unset_key_handler(self, exp_win):
        # deactivate custom keys handling
        exp_win.winHandle.on_key_press = event._onPygletKey
        # del exp_win.winHandle.on_key_release

    def _handle_controller_presses(self, exp_win, keys):
        exp_win.winHandle.dispatch_events()
        global _keyPressBuffer, _keyReleaseBuffer

        key_pressed, key_released, other_keys = None, None, []
        for k in _keyReleaseBuffer:
            if k[0] in keys:
                key_released = k
            self.pressed_keys.discard(k[0])
            logging.data(f"Keyrelease: {k[0]}", t=k[1])
        _keyReleaseBuffer.clear()
        for k in _keyPressBuffer:
            if k[0] in keys:
                key_pressed = k
            self.pressed_keys.add(k[0])
        self._new_key_pressed = _keyPressBuffer[:] #copy
        _keyPressBuffer.clear()
        return key_pressed, key_released, other_keys

    def _run(self, exp_win, ctl_win):


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
            keypresses = event.getKeys(self.RESPONSE_KEYS) # flush response keys
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

            utils.wait_until(self.task_timer, trial["offset_flip"] + RESPONSE_TIME - 1 / config.FRAME_RATE)
            key_pressed, key_released, other_keys = self._handle_controller_presses(exp_win, [trial['key']])
            trial['key_press_time'] = key_pressed[0] if key_pressed
            trial['key_release_time'] = key_released[0] if key_released
            trial['other_keys'] = other_keys if len(other_keys) # log to exclude trial with confounded keys
