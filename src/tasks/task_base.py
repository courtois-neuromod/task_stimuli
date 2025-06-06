import os
import tqdm
import time
import pandas
from psychopy import logging, visual, core, event

from ..shared import fmri, meg, eeg, config


class Task(object):

    DEFAULT_INSTRUCTION = ""
    PROGRESS_BAR_FORMAT = '{l_bar}{bar}{r_bar}'

    def __init__(self, name, instruction=None, use_eyetracking=False, et_calibrate=True):
        self.name = name
        self.use_eyetracking = use_eyetracking
        self.et_calibrate = et_calibrate
        if instruction is None:
            self.instruction = self.__class__.DEFAULT_INSTRUCTION
        else:
            self.instruction = instruction
        self._task_completed = False

        self.flags = 0

    # setup large files for accurate start with other recordings (scanner, biopac...)
    def setup(
        self,
        exp_win,
        output_path,
        output_fname_base,
        use_fmri=False,
        use_meg=False,
        use_eeg=False,
    ):
        self.output_path = output_path
        self.output_fname_base = output_fname_base
        self.use_fmri = use_fmri
        self.use_meg = use_meg
        self.use_eeg = use_eeg
        self._events = []

        self._exp_win_first_flip_time = None
        self._exp_win_last_flip_time = None
        self._ctl_win_last_flip_time = None
        self._task_completed = False
        self._extra_markers = 0

        self._setup(exp_win)
        self._init_progress_bar()

    # initialize a progress bar if we know the duration of the task
    def _init_progress_bar(self):
        self.progress_bar = (
            tqdm.tqdm(total=self.duration,
            bar_format=self.PROGRESS_BAR_FORMAT,
            ) if hasattr(self, "duration") else False
        )
        if not hasattr(self, "_progress_bar_refresh_rate"):
            self._progress_bar_refresh_rate = config.FRAME_RATE

        if meg.MEG_MARKERS_ON_FLIP and self.use_meg:
            meg.send_signal(0)
        if eeg.EEG_MARKERS_ON_FLIP and self.use_eeg:
            eeg.send_signal(0)

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
            ctl_win.timeOnFlip(self, '_ctl_win_last_flip_time')
            ctl_win.flip(clearBuffer=clearBuffer)

        if not clearBuffer is None:
            exp_win.flip(clearBuffer=clearBuffer)
            # set callback for next flip, to be the first callback for other callbacks to use
            exp_win.timeOnFlip(self, '_exp_win_last_flip_time')

    def instructions(self, exp_win, ctl_win):
        if hasattr(self, "_instructions"):
            for clearBuffer in self._instructions(exp_win, ctl_win):
                yield
                if clearBuffer is not None:
                    self._flip_all_windows(exp_win, ctl_win, clearBuffer)
        # 2 flips to clear screen
        for i in range(2):
            yield
            self._flip_all_windows(exp_win, ctl_win, True)

    def run(self, exp_win, ctl_win):
        # needs to be the 1rst callbacks
        exp_win.timeOnFlip(self, '_exp_win_first_flip_time')
        self._flip_all_windows(exp_win, ctl_win, True)
        #sync to first screen flip
        self.task_timer = core.MonotonicClock(self._exp_win_first_flip_time)

        if self.progress_bar:
            self.progress_bar.reset()
        flip_idx = 0

        for clearBuffer in self._run(exp_win, ctl_win):
            # yield first to allow external draw before flip
            yield

            if meg.MEG_MARKERS_ON_FLIP and self.use_meg:
                exp_win.callOnFlip(meg.send_signal, self.flags | (flip_idx%2))
            if eeg.EEG_MARKERS_ON_FLIP and self.use_eeg:
                exp_win.callOnFlip(eeg.send_signal, self.flags | (flip_idx%2))

            if clearBuffer is not None:
                self._flip_all_windows(exp_win, ctl_win, clearBuffer)

            # increment the progress bar depending on task flip rate
            if self.progress_bar:
                if self._progress_bar_refresh_rate and flip_idx % self._progress_bar_refresh_rate == 0:
                    self.progress_bar.update(1)
            flip_idx += 1
        self._task_completed = True

    def stop(self, exp_win, ctl_win):
        if hasattr(self, "_stop"):
            for clearBuffer in self._stop(exp_win, ctl_win):
                yield
                if clearBuffer is not None:
                    self._flip_all_windows(exp_win, ctl_win, clearBuffer)
        if self.progress_bar:
            self.progress_bar.clear()
            self.progress_bar.close()
        # 2 flips to clear screen and backbuffer
        for i in range(2):
            self._flip_all_windows(exp_win, ctl_win, True)


    def restart(self):
        if self.progress_bar:
            self.progress_bar.clear()
            self.progress_bar.close()
            self._init_progress_bar()
        if hasattr(self, "_restart"):
            self._restart()

    def _log_event(self, event, clock='task'):
        if clock == 'task':
            onset = self.task_timer.getTime()
        elif clock == 'flip':
            onset = self._exp_win_last_flip_time - self._exp_win_first_flip_time
        event.update({"onset": onset, "sample": time.monotonic()})
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
