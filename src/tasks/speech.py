import os, sys, time
from psychopy import visual, core, data, logging
from .task_base import Task

from ..shared import config

STIMULI_DURATION = 4
BASELINE_BEGIN = 5
BASELINE_END = 5
ISI = 4


class Speech(Task):

    DEFAULT_INSTRUCTION = """You will be presented text that you need to read out loud right when you see it."""

    def __init__(self, words_file, *args, **kwargs):
        super().__init__(**kwargs)
        if os.path.exists(words_file):
            self.words_file = words_file
            self.words_list = data.importConditions(self.words_file)
        else:
            raise ValueError("File %s does not exists" % words_file)

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

        self.trials = data.TrialHandler(self.words_list, 1, method="random")

        text = visual.TextStim(exp_win, text="", alignText="center", color="white")

        exp_win.logOnFlip(
            level=logging.EXP, msg="speech: task starting at %f" % time.time()
        )

        for frameN in range(config.FRAME_RATE * BASELINE_BEGIN):
            yield ()
        for trial in self.trials:
            text.text = trial["text"]
            exp_win.logOnFlip(level=logging.EXP, msg="speech: %s" % text.text)
            trial["onset"] = self.task_timer.getTime()
            for frameN in range(config.FRAME_RATE * STIMULI_DURATION):
                text.draw(exp_win)
                if ctl_win:
                    text.draw(ctl_win)
                yield ()
            trial["offset"] = self.task_timer.getTime()
            trial["duration"] = trial["offset"] - trial["onset"]
            exp_win.logOnFlip(level=logging.EXP, msg="speech: rest")
            for frameN in range(config.FRAME_RATE * ISI):
                yield ()
        for frameN in range(config.FRAME_RATE * BASELINE_END):
            yield ()

    def _save(self):
        self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
        return False
