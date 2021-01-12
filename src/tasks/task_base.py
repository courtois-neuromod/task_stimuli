import os
import tqdm
import time
import pandas
from psychopy import logging, visual, core, event

from ..shared import fmri, meg, config


class Task(object):

    DEFAULT_INSTRUCTION = ""

    def __init__(self, name, instruction=None):
        self.name = name
        self.use_eyetracking = False
        if instruction is None:
            self.instruction = self.__class__.DEFAULT_INSTRUCTION
        else:
            self.instruction = instruction

    # setup large files for accurate start with other recordings (scanner, biopac...)
    def setup(
        self,
        exp_win,
        output_path,
        output_fname_base,
        use_fmri=False,
        use_eyetracking=False,
        use_meg=False,
    ):
        self.output_path = output_path
        self.output_fname_base = output_fname_base
        self.use_fmri = use_fmri
        self.use_meg = use_meg
        self.use_eyetracking = use_eyetracking
        self._events = []
        self._setup(exp_win)
        # initialize a progress bar if we know the duration of the task
        self.progress_bar = (
            tqdm.tqdm(total=self.duration) if hasattr(self, "duration") else False
        )
        if not hasattr(self, "_progress_bar_refresh_rate"):
            self._progress_bar_refresh_rate = config.FRAME_RATE

    def _setup(self, exp_win):
        pass

    def _generate_unique_filename(self, suffix, ext="tsv"):
        fname = os.path.join(
            self.output_path, f"{self.output_fname_base}_{self.name}_{suffix}.{ext}"
        )
        fi = 1
        while os.path.exists(fname):
            fname = os.path.join(
                self.output_path,
                f"{self.output_fname_base}_{self.name}_{suffix}-{fi:03d}.{ext}",
            )
            fi += 1
        return fname

    def unload(self):
        pass

    def __str__(self):
        return "%s : %s" % (self.__class__, self.name)

    def _flip_all_windows(self, exp_win, ctl_win=None, clearBuffer=True):
        if not ctl_win is None:
            self._ctl_win_last_flip_time = ctl_win.flip(clearBuffer=clearBuffer)
        self._exp_win_last_flip_time = exp_win.flip(clearBuffer=clearBuffer)

    def instructions(self, exp_win, ctl_win):
        if hasattr(self, "_instructions"):
            for clearBuffer in self._instructions(exp_win, ctl_win):
                yield
                self._flip_all_windows(exp_win, ctl_win, clearBuffer)
        # last/only flip to clear screen
        yield
        self._flip_all_windows(exp_win, ctl_win, True)

    def run(self, exp_win, ctl_win):

        self.task_timer = core.Clock()
        frame_idx = 0

        for clearBuffer in self._run(exp_win, ctl_win):
            # yield first to allow external draw before flip
            yield
            self._flip_all_windows(exp_win, ctl_win, clearBuffer)
            if not hasattr(self, "_exp_win_first_flip_time"):
                self._exp_win_first_flip_time = self._exp_win_last_flip_time
            # increment the progress bar every second
            if self.progress_bar:
                frame_idx += 1
                if not frame_idx % self._progress_bar_refresh_rate:
                    self.progress_bar.update(1)

        if self.progress_bar:
            self.progress_bar.clear()
            self.progress_bar.close()

    def stop(self, exp_win, ctl_win):
        if hasattr(self, "_stop"):
            for clearBuffer in self._stop(exp_win, ctl_win):
                yield
                self._flip_all_windows(exp_win, ctl_win, clearBuffer)
        # 2 flips to clear screen and backbuffer
        for i in range(2):
            self._flip_all_windows(exp_win, ctl_win, True)

    def restart(self):
        if hasattr(self, "_restart"):
            self._restart()

    def _log_event(self, event):
        event.update({"onset": self.task_timer.getTime(),"sample":time.monotonic()})
        self._events.append(event)

    def _save(self):
        # to be overriden
        # return False if events need not be saved
        # allow to override events saving if transformation are needed
        pass

    def save(self):
        # call custom task _save()
        save_events = self._save()
        if save_events is None and len(self._events):
            fname = self._generate_unique_filename("events", "tsv")
            df = pandas.DataFrame(self._events)
            df.to_csv(fname, sep="\t", index=False)


class Pause(Task):
    def __init__(self, text="Taking a short break, relax...", **kwargs):
        self.wait_key = kwargs.pop("wait_key", False)
        if not "name" in kwargs:
            kwargs["name"] = "Pause"
        super().__init__(**kwargs)
        self.text = text

    def _setup(self, exp_win):
        self.use_fmri = False
        self.use_eyetracking = False
        super()._setup(exp_win)

    def _run(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win,
            text=self.text,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )

        while True:
            if not self.wait_key is False:
                if len(event.getKeys(self.wait_key)):
                    break
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield True

    def _stop(self, exp_win, ctl_win):
        yield True


class Fixation(Task):

    DEFAULT_INSTRUCTION = """We are going to acquired resting-state data.
Please keep your eyes open and fixate the cross.
Do not think about something in particular, let your mind wander..."""

    def __init__(self, duration=7 * 60, symbol="+", **kwargs):
        if not "name" in kwargs:
            kwargs["name"] = "Pause"
        super().__init__(**kwargs)
        self.duration = duration
        self.symbol = symbol

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
            yield True

    def _run(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win, text=self.symbol, alignText="center", color="white"
        )
        screen_text.height = 0.2

        for frameN in range(config.FRAME_RATE * self.duration):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield True
