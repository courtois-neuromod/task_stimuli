import os, sys, time
from psychopy import visual, core, data, logging
from .task_base import Task

from ..shared import config

STIMULI_DURATION = 4
BASELINE_BEGIN = 5
BASELINE_END = 5
ISI = 1
IMAGES_FOLDER = "/home/basile/data/projects/task_stimuli/BOLD5000_Stimuli/Scene_Stimuli/Presented_Stimuli/ImageNet"

STIMULI_SIZE = (400, 400)

quadrant_id_to_pos = [(-200, 100), (200, 100), (-200, -100), (200, -100)]


class ImagePosition(Task):

    DEFAULT_INSTRUCTION = """You will be presented a set of items in different quadrant of the screen.
Try to remember the items and their location on the screen."""

    def __init__(self, items_list, *args, **kwargs):
        super().__init__(**kwargs)
        # TODO: image lists as params, subjects ....
        self.item_list = data.importConditions(items_list)

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

        trials = data.TrialHandler(self.item_list, 1, method="sequential")
        img = visual.ImageStim(exp_win, size=STIMULI_SIZE, units="pixels")
        exp_win.logOnFlip(
            level=logging.EXP, msg="memory: task starting at %f" % time.time()
        )
        for frameN in range(config.FRAME_RATE * BASELINE_BEGIN):
            yield ()
        for trial in trials:
            image_path = trial["image_path"]
            img.image = image_path
            img.pos = quadrant_id_to_pos[trial["quadrant"]]
            exp_win.logOnFlip(
                level=logging.EXP,
                msg="memory: display %s in quadrant %d"
                % (image_path, trial["quadrant"]),
            )
            for frameN in range(config.FRAME_RATE * STIMULI_DURATION):
                img.draw(exp_win)
                if ctl_win:
                    img.draw(ctl_win)
                yield ()
            exp_win.logOnFlip(level=logging.EXP, msg="memory: rest")
            for frameN in range(config.FRAME_RATE * ISI):
                yield ()
        for frameN in range(config.FRAME_RATE * BASELINE_END):
            yield ()
