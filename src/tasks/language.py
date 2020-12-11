import os, sys, time
from psychopy import visual, core, data, logging, event
from .task_base import Task

from ..shared import config

STIMULI_DURATION = 4
BASELINE_BEGIN = 5
BASELINE_END = 5
TRIPLET_RIGHT_KEY = "l"
TRIPLET_LEFT_KEY = "d"
ISI = 2


class Triplet(Task):

    DEFAULT_INSTRUCTION = """You will be presented three words.

The one on top is the target.
The two below are possible responses.

You have to select the response (left or right) that is closest to the target."""

    INSTRUCTION_WAIT_KEY = (
        DEFAULT_INSTRUCTION + "\nWhen you're ready press <%s>" % TRIPLET_LEFT_KEY
    )

    def __init__(self, words_file, *args, **kwargs):
        self.wait_key = kwargs.pop("wait_key", False)
        super().__init__(**kwargs)
        if self.wait_key:
            self.instruction = Triplet.INSTRUCTION_WAIT_KEY
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

        def _draw_instr():
            screen_text.draw(exp_win)
            if ctl_win:

                screen_text.draw(ctl_win)

        if self.wait_key:
            while True:
                if len(event.getKeys([TRIPLET_LEFT_KEY])):
                    break
                _draw_instr()
                yield
        else:
            for frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
                _draw_instr()
                yield

    def _run(self, exp_win, ctl_win):

        self.trials = data.TrialHandler(self.words_list, 1, method="random")

        target_stim = visual.TextStim(
            exp_win, text="", pos=(0, 0.25), alignText="center", color="white"
        )

        r1_stim = visual.TextStim(
            exp_win, text="", pos=(-0.5, -0.25), alignText="center", color="white"
        )

        r2_stim = visual.TextStim(
            exp_win, text="", pos=(0.5, -0.25), alignText="center", color="white"
        )

        exp_win.logOnFlip(
            level=logging.EXP, msg="triplet: task starting at %f" % time.time()
        )

        for frameN in range(config.FRAME_RATE * BASELINE_BEGIN):
            yield ()
        for trial_idx, trial in enumerate(self.trials):
            target_stim.text = trial["target"]
            r1_stim.text = trial["response1"]
            r2_stim.text = trial["response2"]

            exp_win.logOnFlip(level=logging.EXP, msg="triplet: %d" % trial_idx)
            onset = self.task_timer.getTime()
            # flush keys pressed before
            event.getKeys([TRIPLET_LEFT_KEY, TRIPLET_RIGHT_KEY])
            for frameN in range(config.FRAME_RATE * STIMULI_DURATION):
                triplet_answer_keys = event.getKeys(
                    [TRIPLET_LEFT_KEY, TRIPLET_RIGHT_KEY]
                )
                if len(triplet_answer_keys):
                    self.trials.addData("answer", triplet_answer_keys[0])
                    for frameNN in range(frameN, config.FRAME_RATE * STIMULI_DURATION):
                        yield ()
                    break
                for stim in [target_stim, r1_stim, r2_stim]:
                    stim.draw(exp_win)
                    if ctl_win:
                        stim.draw(ctl_win)
                yield ()
            else:
                self.trials.addData("answer", "")  # no answer, too slow or asleep
            offset = self.task_timer.getTime()
            self.trials.addData("onset", onset)
            self.trials.addData("offset", offset)
            self.trials.addData("duration", offset - onset)  # RT or max stim duration
            exp_win.logOnFlip(level=logging.EXP, msg="triplet: rest")
            for frameN in range(config.FRAME_RATE * ISI):
                yield ()
        for frameN in range(config.FRAME_RATE * BASELINE_END):
            yield ()

    def _save(self):
        self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
        return False
