import os, sys, time
from psychopy import visual, core, data, logging, event
from pandas import read_csv
from .task_base import Task

from ..shared import config, utils

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


class Reading(Task):

    DEFAULT_INSTRUCTION = """You will be presented a text to read word by word."""

    def __init__(self, words_file, word_duration=0.5, cross_duration=20,
                 txt_color="black", txt_font="Palatino Linotype", txt_size=42,
                 bg_color=(.5, .5, .5), *args, **kwargs):
        super().__init__(**kwargs)
        if os.path.exists(words_file):
            self.words_file = words_file
            self.word_duration = word_duration
            self.cross_duration = cross_duration
            self.txt_color = txt_color
            self.txt_font = txt_font
            self.txt_size = txt_size
            self.bg_color = bg_color
            import pandas
            self.words_list = pandas.read_csv(words_file, sep="\t")
            self.duration = len(self.words_list)
        else:
            raise ValueError("File %s does not exists" % words_file)

    def _instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="black",
            wrapWidth=1.2,
        )
        exp_win.setColor(self.bg_color, "rgb")
        if ctl_win:
            ctl_win.setColor(self.bg_color, "rgb")

        for frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield ()

    def _setup(self, exp_win):

        self.txt_stim = visual.TextStim(
            exp_win,
            text="+",
            font=self.txt_font,
            height=self.txt_size,
            units='pixels',
            alignText="center",
            color=self.txt_color,
        )
        self._progress_bar_refresh_rate = 1 # 1 flip / trial

    def _run(self, exp_win, ctl_win):

        # Display each word
        for trial_n, trial in self.words_list.iterrows():
            self.txt_stim.text = trial["word"]
            self.txt_stim._pygletTextObj.set_style('italic', trial["format"] == "italic")
            self.txt_stim.draw(exp_win)
            self.progress_bar.set_description(f"Trial {trial_n}:: {trial['word']} {trial['format']}")
            utils.wait_until(
                self.task_timer,
                trial["onset"] - 1 / config.FRAME_RATE,
                hogCPUperiod=0.2)
            yield True  # flip
            self.words_list.at[trial_n, "onset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )
            if trial_n > 0:
                self.words_list.at[trial_n - 1, "offset_flip"] = self.words_list.at[trial_n, "onset_flip"]
                self.words_list.at[trial_n -1, "duration_flip"] = (
                    self.words_list.at[trial_n - 1, "offset_flip"]
                    - self.words_list.at[trial_n - 1, "onset_flip"]
                )
        # wait for last event duration
        utils.wait_until(
            self.task_timer,
            trial["onset"]+trial["duration"] - 1 / config.FRAME_RATE
        )
        yield

    def _stop(self, exp_win, ctl_win):
        exp_win.setColor((0,0,0), "rgb")
        for _ in range(2):
            yield True

    def _save(self):
        #self.words_list.saveAsWideText(self._generate_unique_filename("events", "tsv")
        self.words_list.to_csv(
            self._generate_unique_filename("events", "tsv"),
            sep = '\t',
            index = False,

        )
        return False
