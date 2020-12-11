import os, sys, time
from psychopy import visual, core, data, logging
from .task_base import Task

from ..shared import config

STIMULI_DURATION = 3
BASELINE_BEGIN = 5
BASELINE_END = 5
ISI = 4


class Images(Task):

    DEFAULT_INSTRUCTION = """Please keep your eyes open an focused on the screen all the time.
You will see pictures of scenes and objects."""

    def __init__(self, images_list, images_path, *args, **kwargs):
        super().__init__(**kwargs)
        # TODO: image lists as params, subjects ....
        self.image_names = data.importConditions(images_list)
        if os.path.exists(images_path) and os.path.exists(
            os.path.join(images_path, self.images_names[0]["images_path"])
        ):
            self.images_path = images_path
        else:
            raise ValueError("Cannot find the listed images in %s " % images_path)

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

        self.trials = data.TrialHandler(self.image_names, 1, method="sequential")
        img = visual.ImageStim(exp_win, size=(1, 1), units="height")
        exp_win.logOnFlip(
            level=logging.EXP, msg="image: task starting at %f" % time.time()
        )
        for frameN in range(config.FRAME_RATE * BASELINE_BEGIN):
            yield ()
        for trial in self.trials:
            image_path = os.path.join(self.images_path, trial["image_path"])
            img.image = image_path
            exp_win.logOnFlip(level=logging.EXP, msg="image: display %s" % image_path)
            trial["onset"] = self.task_timer.getTime()
            for frameN in range(config.FRAME_RATE * STIMULI_DURATION):
                img.draw(exp_win)
                if ctl_win:
                    img.draw(ctl_win)
                yield ()
            trial["offset"] = self.task_timer.getTime()
            trial["duration"] = trial["offset"] - trial["onset"]
            exp_win.logOnFlip(level=logging.EXP, msg="image: rest")
            for frameN in range(config.FRAME_RATE * ISI):
                yield ()
        for frameN in range(config.FRAME_RATE * BASELINE_END):
            yield ()

    def _save(self):
        self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
        return False


class BOLD5000Images(Images):
    pass
