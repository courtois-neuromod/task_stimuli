import os, sys, time, random
import numpy as np
import psychopy
from psychopy import visual, core, data, logging, event
from psychopy.hardware import keyboard
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED, STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)
from .task_base import Task
from .task_base import Fixation
psychopy.useVersion('latest')

from ..shared import config

STIMULI_DURATION = 0.5
ISI_base = 3
nback_ISI_base = 2.5
short_ISI_base = 1
IMAGES_FOLDER = "data/multfs/MULTIF_4_stim"


MULTFS_YES_KEY = "x"
MULTFS_NO_KEY = "b"
CONTINUE_KEY = "a"

config.INSTRUCTION_DURATION = 100

# TODO: modify to MRI screen size
screensize = config.EXP_WINDOW["size"]
# print("screensize:", screensize)
triplet_id_to_pos = [(-.5, 0), (.5, 0), ]

# STIMULI_SIZE = (screensize[0], screensize[1]/2)
STIMULI_SIZE = (1.4,.9)
print("stimuli size:", STIMULI_SIZE)

class multfs_base(Task):

    def __init__(self, items_list, *args, **kwargs):
        super().__init__(**kwargs)
        self.item_list = data.importConditions(items_list)
        self.temp_dict = {}
        self.instruction = instructions_converter(self.name)
        self.abbrev_instruction = abbrev_instructions_converter(self.name)
        # print("abbrev instruction:", self.abbrev_instruction)
        self.globalClock = core.Clock() # to track the time since experiment start
        self.routineTimer = core.Clock() # to track time remaining of each (possibly non-slip) routine
        self.frameTolerance = 0.001 # how close to onset before 'same' frame
        self.storage_dict = {}

    def _setup(self, exp_win):
        self.fixation = visual.TextStim(exp_win, text="+", alignText="center", color="white")
        self.next_trial = visual.TextStim(exp_win, text="Next trial!", alignText = "center", color = "white", height = 0.1)
        self.empty_text= visual.TextStim(exp_win, text="", alignText = "center", color = "white", height = 0.1)
        super()._setup(exp_win)

    def _instructions(self, exp_win, ctl_win):
        if ctl_win:
            win = ctl_win
        else:
            win = exp_win
        screen_text_bold = visual.TextStim(
            win=exp_win,
            name='introtext_bold',
            text=self.abbrev_instruction,
            font='Arial',
            pos=(0, 0.2), height=0.1, ori=0,
            color="white", colorSpace='rgb', opacity=1,
            languageStyle='LTR',
            wrapWidth=config.WRAP_WIDTH,
        )
        screen_text = visual.TextStim(
            win = exp_win,
            name = 'introtext',
            text=self.instruction,
            font = 'Arial',
            pos = (0,0), height = 0.05, ori = 0,
            color="white", colorSpace = 'rgb', opacity = 1,
            languageStyle = 'LTR',
            wrapWidth=config.WRAP_WIDTH,
        )

        # -- prepare to start Routine "Intro" --
        # print("start of the task:", self.globalClock.getTime())
        for frameN in range(int(np.floor(config.FRAME_RATE * 1000))):
            screen_text_bold.draw(exp_win)
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text_bold.draw(ctl_win)
                screen_text.draw(ctl_win)

            keys = psychopy.event.getKeys(keyList=['space','a'])
            if keys:
                resp_time = self.globalClock.getTime()
                # print("end of the instruction time:", resp_time) # todo: record response time for reading instructions [an empty dict in the init?]
                if keys[-1] == "space" or 'a':
                    break
            yield ()
        # print("end of the instruction time:", resp_time)

    def _block_intro(self, exp_win, ctl_win, n_trials = 4):
        if ctl_win:
            win = ctl_win
        else:
            win = exp_win
        screen_text_bold = visual.TextStim(
            win=exp_win,
            name='introtext_bold',
            text=self.abbrev_instruction,
            font='Arial',
            pos=(0, 0.2), height=0.1, ori=0,
            color="white", colorSpace='rgb', opacity=1,
            languageStyle='LTR',
            wrapWidth=config.WRAP_WIDTH,
        )
        screen_text = visual.TextStim(
            win=exp_win,
            name='blockintrotext',
            text= 'New Block! \n\nEach block contains %d trials, each starts with fixation. \n\nPress A to continue!' % n_trials, # todo: modify the key instructions
            font='Open Sans',
            pos=(0, 0), height=0.05, ori=0,
            color="white", colorSpace='rgb', opacity=1,
            languageStyle='LTR',
            wrapWidth=config.WRAP_WIDTH,
        )

        # -- prepare to start Routine "Intro" --
        print("start of the block instruction:", self.globalClock.getTime())
        for frameN in range(config.FRAME_RATE * 1000):
            screen_text_bold.draw(exp_win)
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text_bold.draw(ctl_win)
                screen_text.draw(ctl_win)
            keys = psychopy.event.getKeys(keyList=['space', 'x', 'X','a'])

            if keys:
                resp_time = self.globalClock.getTime()
                # print(keys, resp_time) # todo: record response time for reading instructions [an empty dict in the init?]
                if keys[-1] == "space" or "a":
                    win.flip()
                    break
            yield ()
        print("end of the block instruction:", self.globalClock.getTime())

    def _fill_in_blank(self, exp_win, ctl_win, task):
        curr_time = self.globalClock.getTime()
        print("does it work?!")
        print(curr_time)
        if task == "1back":
            for i in range(config.FRAME_RATE * (int(curr_time//config.TR)+1)* config.TR - curr_time + 0.25):
                self.empty_text.draw(exp_win)
                if ctl_win:
                    self.empty_text.draw(ctl_win)
        print(self.globalClock.getTime())
        print("updated starting time:", (self.globalClock.getTime() - 0.25) % config.TR)
        yield()


    def _block_end(self, exp_win, ctl_win):
        if ctl_win:
            win = ctl_win
        else:
            win = exp_win
        screen_text = visual.TextStim(
            win=exp_win,
            name='blockendtext',
            text= 'End of the block! \n\nPress A to start next block', # todo: modify the key instructions
            font='Open Sans',
            pos=(0, 0), height=0.05, ori=0,
            color="white", colorSpace='rgb', opacity=1,
            languageStyle='LTR',
            wrapWidth=config.WRAP_WIDTH,
        )

        # -- prepare to start Routine "Intro" --

        for frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            keys = psychopy.event.getKeys(keyList=['space', 'x', 'X','a'])
            if keys:
                resp_time = self.globalClock.getTime()
                # print(keys, resp_time) # todo: record response time for reading instructions [an empty dict in the init?]
                if keys[-1] == "space" or "a":
                    exp_win.flip()
                    break
            yield ()

    def _save(self):
        if hasattr(self, 'trials'):
            self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
        return None


class multfs_dms(multfs_base):

    def __init__(self, items_list, feature = "loc", session = None, **kwargs):
        super().__init__(items_list, **kwargs)
        if "subtraining" in items_list:
            self.n_trials = 4
            self.n_blocks = 2
        else:
            self.n_trials = 8
            self.n_blocks = 2

        self.feature = feature
        self.session = session # todo: add progress bar

        self.seq_len = 2

    def _run(self, exp_win, ctl_win):
        self.trials = data.TrialHandler(self.item_list, 1, method="random")
        exp_win.logOnFlip(
            level=logging.EXP, msg="memory: task starting at %f" % time.time()
        )
        n_blocks = self.n_blocks # TODO: CHANGE THE NUMBER OF BLOCKS PER TASK VARIATION

        for block in range(n_blocks):
            for clearBuffer in self._block_intro(exp_win, ctl_win, self.n_trials):
                self._flip_all_windows(exp_win, ctl_win, clearBuffer)
            # 2 flips to clear screen
            for i in range(2):
                yield True

            img = visual.ImageStim(exp_win, size=STIMULI_SIZE, units="norm")

            trial_idx = 0
            for trial in self.trials:
                exp_win.logOnFlip(level=logging.EXP, msg="multfs-dms_%s: block %d trial %d" % (self.feature, block, trial_idx))
                trial_idx += 1
                for i in range(2):
                    yield True

                for n_stim in range(1, 1+self.seq_len):
                    img.image = IMAGES_FOLDER + "/" + str(trial["objmod%s" % str(n_stim)]) + "/image.png"
                    img.pos = triplet_id_to_pos[trial["loc%s" % str(n_stim)]]

                    for i in range(2):
                        yield True

                    self.trials.addData("stimulus_%d_onset" % n_stim, self.globalClock.getTime())
                    for frameN in range(int(config.FRAME_RATE * (STIMULI_DURATION + ISI_base))):
                        multfs_answer_keys = psychopy.event.getKeys(
                            [MULTFS_YES_KEY, MULTFS_NO_KEY, 'space'], timeStamped=True
                        )
                        if len(multfs_answer_keys):

                            self.trials.addData("response_%d" % n_stim, multfs_answer_keys[-1][0])
                            self.trials.addData("response_%d_time_key" % n_stim, multfs_answer_keys[-1][1])
                            self.trials.addData("response_%d_time_global" % n_stim, self.globalClock.getTime())
                            if n_stim == self.seq_len:
                                break

                        if frameN <= int(config.FRAME_RATE * STIMULI_DURATION):
                            img.draw()
                            if frameN == int(config.FRAME_RATE * STIMULI_DURATION):
                                self.trials.addData("stimulus_%d_offset" % n_stim, self.globalClock.getTime())

                        if n_stim == 1:
                            self.fixation.draw()

                        self._flip_all_windows(exp_win, ctl_win)

                yield ()

                for frameN in range(int(config.FRAME_RATE * ISI_base/3)):
                    self.next_trial.draw()
                    yield True
                for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
                    self.empty_text.draw()
                    yield True

                # print("current trial idx:", trial_idx)
                # print("total number of trials:", self.n_trials)
                if trial_idx >= self.n_trials:
                    self.trials.addData("trial_end", self.task_timer.getTime())
                    break

            for clearBuffer in self._block_end(exp_win, ctl_win):
                self._flip_all_windows(exp_win, ctl_win, clearBuffer)

            for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
                self.empty_text.draw()
                yield True




class multfs_1back(multfs_base):

    def __init__(self, items_list, feature = "loc", seq_len=6, session = None, **kwargs):
        super().__init__(items_list, **kwargs)
        self.seq_len = seq_len
        self.feature = feature
        self.session = session # todo: add progress bar
        if "subtraining" in items_list:
            self.n_trials = 2
            self.n_blocks = 1
        else:
            self.n_trials = 4
            self.n_blocks = 4

    def _run(self, exp_win, ctl_win):
        self.trials = data.TrialHandler(self.item_list, 1, method="random")
        exp_win.logOnFlip(
            level=logging.EXP, msg="memory: task starting at %f" % time.time()
        )
        n_blocks = self.n_blocks # TODO: CHANGE THE NUMBER OF BLOCKS PER TASK VARIATION

        for block in range(n_blocks):
            for clearBuffer in self._block_intro(exp_win, ctl_win, self.n_trials):
                self._flip_all_windows(exp_win, ctl_win, clearBuffer)
            # 2 flips to clear screen
            for i in range(2):
                yield True

            img = visual.ImageStim(exp_win, size=STIMULI_SIZE, units="norm")

            trial_idx = 0
            for trial in self.trials:
                exp_win.logOnFlip(level=logging.EXP, msg="multfs-1back_%s: block %d trial %d" % (self.feature, block, trial_idx))
                trial_idx += 1
                for i in range(2):
                    yield True
                # print("beginning of the alignment")
                # self._fill_in_blank(exp_win, ctl_win, task="1back")
                curr_time = self.globalClock.getTime()
                # print("does it work?!")
                # print("before alignment:",curr_time)


                thres_time = (int(curr_time / config.TR) + 1) * config.TR + 0.25

                while True:
                    if self.globalClock.getTime() >= thres_time:
                        break
                # for i in range(int(config.FRAME_RATE * ((int(curr_time // config.TR) + 1) * config.TR - curr_time + 0.25))):
                #     print(i)
                #     self.empty_text.draw(exp_win)
                #     if ctl_win:
                #         self.empty_text.draw(ctl_win)
                # print("end of the alignment")
                # print(self.globalClock.getTime())
                # print("updated starting time:", (self.globalClock.getTime() - 0.25) % config.TR)
                for n_stim in range(1, 1+self.seq_len):
                    img.image = IMAGES_FOLDER + "/" + str(trial["objmod%s" % str(n_stim)]) + "/image.png"
                    img.pos = triplet_id_to_pos[trial["loc%s" % str(n_stim)]]

                    for i in range(2):
                        yield True


                    self.trials.addData("stimulus_%d_onset" % n_stim, self.globalClock.getTime())


                    for frameN in range(int(config.FRAME_RATE * (STIMULI_DURATION + nback_ISI_base))):
                        multfs_answer_keys = psychopy.event.getKeys(
                            [MULTFS_YES_KEY, MULTFS_NO_KEY, 'space'], timeStamped=True
                        )

                        if len(multfs_answer_keys):
                            self.trials.addData("response_%d" % n_stim, multfs_answer_keys[-1][0])
                            self.trials.addData("response_%d_time_key" % n_stim, multfs_answer_keys[-1][1])
                            self.trials.addData("response_%d_time_global" % n_stim, self.globalClock.getTime())
                            if n_stim == self.seq_len:
                                break

                        if frameN <= int(config.FRAME_RATE * STIMULI_DURATION):
                            img.draw()
                            if frameN == int(config.FRAME_RATE * STIMULI_DURATION):
                                self.trials.addData("stimulus_%d_offset" % n_stim, self.globalClock.getTime())
                        if n_stim == 1:
                            self.fixation.draw()

                        self._flip_all_windows(exp_win, ctl_win)

                yield True

                for frameN in range(int(config.FRAME_RATE * ISI_base/3)):
                    self.next_trial.draw()
                    yield True
                for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
                    self.empty_text.draw()
                    yield True

                if trial_idx > self.n_trials:
                    self.trials.addData("trial_end", self.task_timer.getTime())
                    break

            for clearBuffer in self._block_end(exp_win, ctl_win):
                self._flip_all_windows(exp_win, ctl_win, clearBuffer)

            for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
                self.empty_text.draw()
                yield True

class multfs_CTXDM(multfs_base):

    def __init__(self, items_list, feature = "lco", seq_len=3, session = None, **kwargs):
        super().__init__(items_list, **kwargs)
        self.seq_len = seq_len
        self.feature = feature
        self.session = session # todo: add progress bar

        if "subtraining" in items_list:
            self.n_trials = 3
            self.n_blocks = 2
        else:
            self.n_trials = 10
            self.n_blocks = 6

    def _run(self, exp_win, ctl_win):
        self.trials = data.TrialHandler(self.item_list, 1, method="random")
        exp_win.logOnFlip(
            level=logging.EXP, msg="memory: task starting at %f" % time.time()
        )
        n_blocks = self.n_blocks # TODO: CHANGE THE NUMBER OF BLOCKS PER TASK VARIATION

        for block in range(n_blocks):
            for clearBuffer in self._block_intro(exp_win, ctl_win, self.n_trials):
                self._flip_all_windows(exp_win, ctl_win, clearBuffer)
            # 2 flips to clear screen
            for i in range(2):
                yield True

            img = visual.ImageStim(exp_win, size=STIMULI_SIZE, units="norm")

            trial_idx = 0
            for trial in self.trials:
                exp_win.logOnFlip(level=logging.EXP, msg="multfs-ctxdm_%s: block %d trial %d" % (self.feature, block, trial_idx))
                trial_idx += 1
                for i in range(2):
                    yield True

                thres_time = (int(self.globalClock.getTime() / config.TR) + 1) * config.TR + 0.5
                # print("before alignment:", self.globalClock.getTime())
                while True:
                    if self.globalClock.getTime() >= thres_time:
                        break
                # print("after alignment:", self.globalClock.getTime())
                for n_stim in range(1, 1+self.seq_len):
                    img.image = IMAGES_FOLDER + "/" + str(trial["objmod%s" % str(n_stim)]) + "/image.png"
                    img.pos = triplet_id_to_pos[trial["loc%s" % str(n_stim)]]

                    for i in range(2):
                        yield True


                    self.trials.addData("stimulus_%d_onset" % n_stim, self.globalClock.getTime())

                    if n_stim == 1:
                        for frameN in range(int(config.FRAME_RATE * (STIMULI_DURATION + short_ISI_base))):

                            if frameN <= int(config.FRAME_RATE * STIMULI_DURATION):
                                img.draw()
                                if frameN == int(config.FRAME_RATE * STIMULI_DURATION):
                                    self.trials.addData("stimulus_%d_offset" % n_stim, self.globalClock.getTime())

                            self.fixation.draw()
                            self._flip_all_windows(exp_win, ctl_win)
                    else:
                        for frameN in range(int(config.FRAME_RATE * (STIMULI_DURATION + ISI_base))):
                            multfs_answer_keys = psychopy.event.getKeys(
                                [MULTFS_YES_KEY, MULTFS_NO_KEY, 'space'], timeStamped=True
                            )

                            if len(multfs_answer_keys):
                                self.trials.addData("response_%d" % n_stim, multfs_answer_keys[-1][0])
                                self.trials.addData("response_%d_time_key" % n_stim, multfs_answer_keys[-1][1])
                                self.trials.addData("response_%d_time_global" % n_stim, self.globalClock.getTime())
                                if n_stim == self.seq_len:
                                    break

                            if frameN <= int(config.FRAME_RATE * STIMULI_DURATION):
                                img.draw()
                                if frameN == int(config.FRAME_RATE * STIMULI_DURATION):
                                    self.trials.addData("stimulus_%d_offset" % n_stim, self.globalClock.getTime())

                            self._flip_all_windows(exp_win, ctl_win)

                yield ()

                for frameN in range(int(config.FRAME_RATE * ISI_base/3)):
                    self.next_trial.draw()
                    yield True
                for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
                    self.empty_text.draw()
                    yield True

                if trial_idx > self.n_trials:
                    self.trials.addData("trial_end", self.task_timer.getTime())
                    break

            for clearBuffer in self._block_end(exp_win, ctl_win):
                self._flip_all_windows(exp_win, ctl_win, clearBuffer)

            for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
                self.empty_text.draw()
                yield True



class multfs_interdms_ABAB(multfs_base):

    def __init__(self, items_list, feature = "loc", pattern = "ABAB", seq_len=4, session = None, **kwargs):
        super().__init__(items_list, **kwargs)
        self.seq_len = seq_len
        self.feature = feature
        self.pattern = pattern
        self.session = session # todo: add progress bar
        if "subtraining" in items_list:
            self.n_trials = 2
            self.n_blocks = 2
        else:
            self.n_trials = 6
            self.n_blocks = 6


    def _run(self, exp_win, ctl_win):
        self.trials = data.TrialHandler(self.item_list, 1, method="random")
        exp_win.logOnFlip(
            level=logging.EXP, msg="memory: task starting at %f" % time.time()
        )
        n_blocks = self.n_blocks # TODO: CHANGE THE NUMBER OF BLOCKS PER TASK VARIATION

        for block in range(n_blocks):
            for clearBuffer in self._block_intro(exp_win, ctl_win, self.n_trials):
                self._flip_all_windows(exp_win, ctl_win, clearBuffer)
            # 2 flips to clear screen
            for i in range(2):
                yield True

            img = visual.ImageStim(exp_win, size=STIMULI_SIZE, units="norm")

            trial_idx = 0
            for trial in self.trials:
                exp_win.logOnFlip(level=logging.EXP, msg="multfs-interdms_%s_%s: block %d trial %d" % (self.pattern, self.feature, block, trial_idx))
                trial_idx += 1
                for i in range(2):
                    yield True

                thres_time = (int(self.globalClock.getTime() / config.TR) + 1) * config.TR + 0.5
                # print("before alignment:", self.globalClock.getTime())
                while True:
                    if self.globalClock.getTime() >= thres_time:
                        break
                # print("after alignment:", self.globalClock.getTime())

                for n_stim in range(1, 1+self.seq_len):
                    img.image = IMAGES_FOLDER + "/" + str(trial["objmod%s" % str(n_stim)]) + "/image.png"
                    img.pos = triplet_id_to_pos[trial["loc%s" % str(n_stim)]]

                    for i in range(2):
                        yield True

                    self.trials.addData("stimulus_%d_onset" % n_stim, self.globalClock.getTime())
                    if n_stim == 1:
                        for frameN in range(int(config.FRAME_RATE * (STIMULI_DURATION + short_ISI_base))):

                            if frameN <= int(config.FRAME_RATE * STIMULI_DURATION):
                                img.draw()
                                if frameN == int(config.FRAME_RATE * STIMULI_DURATION):
                                    self.trials.addData("stimulus_%d_offset" % n_stim, self.globalClock.getTime())

                            self.fixation.draw()
                            self._flip_all_windows(exp_win, ctl_win)
                    else:
                        for frameN in range(int(config.FRAME_RATE * (STIMULI_DURATION + ISI_base))):
                            multfs_answer_keys = psychopy.event.getKeys(
                                [MULTFS_YES_KEY, MULTFS_NO_KEY, 'space'], timeStamped=True
                            )

                            if len(multfs_answer_keys):
                                self.trials.addData("response_%d" % n_stim, multfs_answer_keys[-1][0])
                                self.trials.addData("response_%d_time_key" % n_stim, multfs_answer_keys[-1][1])
                                self.trials.addData("response_%d_time_global" % n_stim, self.globalClock.getTime())
                                if n_stim == self.seq_len:
                                    break

                            if frameN <= int(config.FRAME_RATE * STIMULI_DURATION):
                                img.draw()
                                if frameN == int(config.FRAME_RATE * STIMULI_DURATION):
                                    self.trials.addData("stimulus_%d_offset" % n_stim, self.globalClock.getTime())

                            self._flip_all_windows(exp_win, ctl_win)

                yield ()

                for frameN in range(int(config.FRAME_RATE * ISI_base/3)):
                    self.next_trial.draw()
                    yield True
                for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
                    self.empty_text.draw()
                    yield True

                if trial_idx > self.n_trials:
                    self.trials.addData("trial_end", self.task_timer.getTime())
                    break

            for clearBuffer in self._block_end(exp_win, ctl_win):
                self._flip_all_windows(exp_win, ctl_win, clearBuffer)

            for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
                self.empty_text.draw()
                yield True


class multfs_interdms_ABBA(multfs_base):

    def __init__(self, items_list, feature = "loc", pattern = "ABBA", seq_len=4, session = None, **kwargs):
        super().__init__(items_list, **kwargs)
        self.seq_len = seq_len
        self.feature = feature
        self.pattern = pattern
        self.session = session # todo: add progress bar
        if "subtraining" in items_list:
            self.n_trials = 2
            self.n_blocks = 2
        else:
            self.n_trials = 6
            self.n_blocks = 6

    def _run(self, exp_win, ctl_win):
        self.trials = data.TrialHandler(self.item_list, 1, method="random")
        exp_win.logOnFlip(
            level=logging.EXP, msg="memory: task starting at %f" % time.time()
        )
        n_blocks = self.n_blocks # TODO: CHANGE THE NUMBER OF BLOCKS PER TASK VARIATION

        for block in range(n_blocks):
            for clearBuffer in self._block_intro(exp_win, ctl_win, self.n_trials):
                self._flip_all_windows(exp_win, ctl_win, clearBuffer)
            # 2 flips to clear screen
            for i in range(2):
                yield True

            img = visual.ImageStim(exp_win, size=STIMULI_SIZE, units="norm")

            trial_idx = 0
            for trial in self.trials:
                exp_win.logOnFlip(level=logging.EXP, msg="multfs-interdms_%s_%s: block %d trial %d" % (self.pattern, self.feature, block, trial_idx))
                trial_idx += 1
                for i in range(2):
                    yield True

                thres_time = (int(self.globalClock.getTime() / config.TR) + 1) * config.TR + 0.5
                # print("before alignment:", self.globalClock.getTime())
                while True:
                    if self.globalClock.getTime() >= thres_time:
                        break
                # print("after alignment:", self.globalClock.getTime())

                for n_stim in range(1, 1+self.seq_len):
                    img.image = IMAGES_FOLDER + "/" + str(trial["objmod%s" % str(n_stim)]) + "/image.png"
                    img.pos = triplet_id_to_pos[trial["loc%s" % str(n_stim)]]

                    for i in range(2):
                        yield True


                    self.trials.addData("stimulus_%d_onset" % n_stim, self.globalClock.getTime())
                    if n_stim == 1:
                        for frameN in range(int(config.FRAME_RATE * (STIMULI_DURATION + short_ISI_base))):

                            if frameN <= int(config.FRAME_RATE * STIMULI_DURATION):
                                img.draw()
                                if frameN == int(config.FRAME_RATE * STIMULI_DURATION):
                                    self.trials.addData("stimulus_%d_offset" % n_stim, self.globalClock.getTime())

                            self.fixation.draw()
                            self._flip_all_windows(exp_win, ctl_win)
                    else:
                        for frameN in range(int(config.FRAME_RATE * (STIMULI_DURATION + ISI_base))):
                            multfs_answer_keys = psychopy.event.getKeys(
                                [MULTFS_YES_KEY, MULTFS_NO_KEY, 'space'], timeStamped=True
                            )

                            if len(multfs_answer_keys):
                                self.trials.addData("response_%d" % n_stim, multfs_answer_keys[-1][0])
                                self.trials.addData("response_%d_time_key" % n_stim, multfs_answer_keys[-1][1])
                                self.trials.addData("response_%d_time_global" % n_stim, self.globalClock.getTime())
                                if n_stim == self.seq_len:
                                    break

                            if frameN <= int(config.FRAME_RATE * STIMULI_DURATION):
                                img.draw()
                                if frameN == int(config.FRAME_RATE * STIMULI_DURATION):
                                    self.trials.addData("stimulus_%d_offset" % n_stim, self.globalClock.getTime())

                            self._flip_all_windows(exp_win, ctl_win)

                yield ()

                for frameN in range(int(config.FRAME_RATE * ISI_base/3)):
                    self.next_trial.draw()
                    yield True
                for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
                    self.empty_text.draw()
                    yield True

                if trial_idx > self.n_trials:
                    self.trials.addData("trial_end", self.task_timer.getTime())
                    break

            for clearBuffer in self._block_end(exp_win, ctl_win):
                self._flip_all_windows(exp_win, ctl_win, clearBuffer)

            for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
                self.empty_text.draw()
                yield True



# class multfs_interdms_AABB(multfs_base):
#
#     def __init__(self, items_list, feature = "loc", session = None, **kwargs):
#         super().__init__(items_list, **kwargs)
#         self.feature = feature
#         self.pattern = "AABB"
#         self.session = session # todo: add progress bar
#
#     def _run(self, exp_win, ctl_win):
#         self.trials = data.TrialHandler(self.item_list, 1, method="random")
#         exp_win.logOnFlip(
#             level=logging.EXP, msg="memory: task starting at %f" % time.time()
#         )
#         n_blocks = 2 # TODO: CHANGE THE NUMBER OF BLOCKS PER TASK VARIATION
#         for block in range(n_blocks):
#             for clearBuffer in self._block_intro(exp_win, ctl_win):
#                 self._flip_all_windows(exp_win, ctl_win, clearBuffer)
#             # 2 flips to clear screen
#             for i in range(2):
#                 yield True
#
#             img = visual.ImageStim(exp_win, size=STIMULI_SIZE, units="norm")
#
#             trial_idx = 0
#             for trial in self.trials:
#                 exp_win.logOnFlip(level=logging.EXP, msg="multfs-interDMS_%s_%s: block %d " % (self.pattern,self.feature, block,))
#
#                 onset = self.task_timer.getTime()
#                 event.getKeys([MULTFS_YES_KEY, MULTFS_NO_KEY, "A", "Y"])
#
#                 trial_idx += 1
#                 for i in range(2):
#                     yield True
#
#                 # print("global time since the start of stim presentation:", self.task_timer.getTime())
#                 self.trials.addData("trial_stim_start",self.task_timer.getTime())
#
#                 n_stim = 1
#                 img.image = IMAGES_FOLDER + "/" + str(trial["frame_obj_%s" % str(n_stim)]) + "/image.png"
#                 if self.feature != "loc":
#                     img.pos = (0, 0)
#                 else:
#                     img.pos = triplet_id_to_pos_ctxdm[trial["frame_loc_%s" % str(n_stim)]]
#
#                 for frameN in range(int(config.FRAME_RATE * STIMULI_DURATION/3)):
#                     yield True
#                     yield True
#                     img.setAutoDraw(True)
#                     self.fixation.setAutoDraw(True)
#                     yield()
#
#
#                 img.setAutoDraw(False)
#                 yield True
#                 yield True
#
#
#                 self.trials.addData("trial_ISI_start", self.task_timer.getTime())
#                 for frameN in range(int(config.FRAME_RATE * ISI_base/3)):
#                     self.fixation.setAutoDraw(True)
#                     yield True
#                     yield True
#                     yield ()
#
#                 self.fixation.setAutoDraw(False)
#                 yield True
#                 yield True
#
#                 n_stim = 2
#                 img.image = IMAGES_FOLDER + "/" + str(trial["frame_obj_%s" % str(n_stim)]) + "/image.png"
#                 if self.feature != "loc":
#                     img.pos = (0, 0)
#                 else:
#                     img.pos = triplet_id_to_pos_ctxdm[trial["frame_loc_%s" % str(n_stim)]]
#
#                 for frameN in range(int(config.FRAME_RATE * STIMULI_DURATION/3)):
#                     img.setAutoDraw(True)
#                     yield True
#                     yield True
#                     yield ()
#
#                 img.setAutoDraw(False)
#                 self.fixation.setAutoDraw(False)
#                 yield True
#                 yield True
#
#                 self.trials.addData("trial_ISI_start", self.task_timer.getTime())
#                 for frameN in range(int(config.FRAME_RATE * ISI_base/3)):
#
#                     self.fixation.setAutoDraw(False)
#                     multfs_answer_keys = event.getKeys(
#                         [MULTFS_YES_KEY, MULTFS_NO_KEY, 'space', 'A', 'Y'], timeStamped=True
#                     )
#                     if len(multfs_answer_keys):
#                         self.trials.addData("response", multfs_answer_keys[-1][0])
#                         self.trials.addData("response_time", multfs_answer_keys[-1][1])
#                         self.trials.addData("response_time_2", self.task_timer.getTime())
#                     yield True
#                     yield True
#                     yield ()
#
#                 n_stim = 3
#                 img.image = IMAGES_FOLDER + "/" + str(trial["frame_obj_%s" % str(n_stim)]) + "/image.png"
#                 if self.feature != "loc":
#                     img.pos = (0, 0)
#                 else:
#                     img.pos = triplet_id_to_pos_ctxdm[trial["frame_loc_%s" % str(n_stim)]]
#
#                 for frameN in range(int(config.FRAME_RATE * STIMULI_DURATION/3)):
#                     yield True
#                     yield True
#                     img.setAutoDraw(True)
#                     self.fixation.setAutoDraw(True)
#                     yield ()
#
#                 img.setAutoDraw(False)
#                 yield True
#                 yield True
#
#                 self.trials.addData("trial_ISI_start", self.task_timer.getTime())
#                 for frameN in range(int(config.FRAME_RATE * ISI_base/3)):
#                     self.fixation.setAutoDraw(True)
#                     yield True
#                     yield True
#                     yield ()
#
#                 self.fixation.setAutoDraw(False)
#                 yield True
#                 yield True
#
#                 n_stim = 4
#                 img.image = IMAGES_FOLDER + "/" + str(trial["frame_obj_%s" % str(n_stim)]) + "/image.png"
#                 if self.feature != "loc":
#                     img.pos = (0, 0)
#                 else:
#                     img.pos = triplet_id_to_pos_ctxdm[trial["frame_loc_%s" % str(n_stim)]]
#
#                 for frameN in range(int(config.FRAME_RATE * STIMULI_DURATION/3)):
#                     img.setAutoDraw(True)
#                     yield True
#                     yield True
#                     yield ()
#
#                 img.setAutoDraw(False)
#                 self.fixation.setAutoDraw(False)
#                 yield True
#                 yield True
#
#                 self.trials.addData("trial_ISI_start", self.task_timer.getTime())
#                 for frameN in range(int(config.FRAME_RATE * ISI_base/3)):
#
#                     self.fixation.setAutoDraw(False)
#                     yield True
#                     yield True
#                     multfs_answer_keys = event.getKeys(
#                         [MULTFS_YES_KEY, MULTFS_NO_KEY, 'space', 'A', 'Y'], timeStamped=True
#                     )
#                     if len(multfs_answer_keys):
#                         self.trials.addData("response", multfs_answer_keys[-1][0])
#                         self.trials.addData("response_time", multfs_answer_keys[-1][1])
#                         self.trials.addData("response_time_2", self.task_timer.getTime())
#                         break
#
#                     yield ()
#
#                 img.setAutoDraw(False)
#                 self.fixation.setAutoDraw(False)
#                 yield True
#                 yield True
#                 for frameN in range(int(config.FRAME_RATE * ISI_base)):
#                     self.next_trial.draw()
#                     yield True
#                 for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
#                     self.empty_text.draw()
#                     yield True
#
#
#                 if trial_idx > 3:
#                     self.trials.addData("trial_end", self.task_timer.getTime())
#                     break
#
#             for clearBuffer in self._block_end(exp_win, ctl_win):
#                 self._flip_all_windows(exp_win, ctl_win, clearBuffer)
#             yield True
#             for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
#                 self.empty_text.draw()
#                 yield True
#     def _save(self):
#         self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
#         return False
#
#
# class multfs_interdms_ABAB(multfs_base):
#
#     def __init__(self, items_list, feature = "loc", session = None, **kwargs):
#         super().__init__(items_list, **kwargs)
#         self.feature = feature
#         self.pattern = "ABAB"
#         self.session = session # todo: add progress bar
#
#     def _run(self, exp_win, ctl_win):
#         self.trials = data.TrialHandler(self.item_list, 1, method="random")
#         exp_win.logOnFlip(
#             level=logging.EXP, msg="memory: task starting at %f" % time.time()
#         )
#         n_blocks = 2 # TODO: CHANGE THE NUMBER OF BLOCKS PER TASK VARIATION
#         for block in range(n_blocks):
#             for clearBuffer in self._block_intro(exp_win, ctl_win):
#                 self._flip_all_windows(exp_win, ctl_win, clearBuffer)
#             # 2 flips to clear screen
#             for i in range(2):
#                 yield True
#
#             img = visual.ImageStim(exp_win, size=STIMULI_SIZE, units="norm")
#
#             trial_idx = 0
#             for trial in self.trials:
#                 exp_win.logOnFlip(level=logging.EXP,
#                                   msg="multfs-interDMS_%s_%s: block %d " % (self.pattern, self.feature, block,))
#
#                 onset = self.task_timer.getTime()
#                 event.getKeys([MULTFS_YES_KEY, MULTFS_NO_KEY, "A", "Y"])
#
#                 trial_idx += 1
#                 for i in range(2):
#                     yield True
#
#                 # print("global time since the start of stim presentation:", self.task_timer.getTime())
#                 self.trials.addData("trial_stim_start",self.task_timer.getTime())
#
#                 n_stim = 1
#                 img.image = IMAGES_FOLDER + "/" + str(trial["frame_obj_%s" % str(n_stim)]) + "/image.png"
#                 if self.feature != "loc":
#                     img.pos = (0, 0)
#                 else:
#                     img.pos = triplet_id_to_pos_ctxdm[trial["frame_loc_%s" % str(n_stim)]]
#
#                 for frameN in range(int(config.FRAME_RATE * STIMULI_DURATION/2)):
#                     yield True
#                     yield True
#                     img.setAutoDraw(True)
#                     self.fixation.setAutoDraw(True)
#                     yield()
#
#
#                 img.setAutoDraw(False)
#                 yield True
#                 yield True
#
#
#                 self.trials.addData("trial_ISI_start", self.task_timer.getTime())
#                 for frameN in range(int(config.FRAME_RATE * ISI_base/2)):
#                     self.fixation.setAutoDraw(True)
#                     yield True
#                     yield True
#                     yield ()
#
#                 self.fixation.setAutoDraw(False)
#                 yield True
#                 yield True
#
#                 n_stim = 2
#                 img.image = IMAGES_FOLDER + "/" + str(trial["frame_obj_%s" % str(n_stim)]) + "/image.png"
#                 if self.feature != "loc":
#                     img.pos = (0, 0)
#                 else:
#                     img.pos = triplet_id_to_pos_ctxdm[trial["frame_loc_%s" % str(n_stim)]]
#
#                 for frameN in range(int(config.FRAME_RATE * STIMULI_DURATION / 2)):
#                     yield True
#                     yield True
#                     img.setAutoDraw(True)
#                     self.fixation.setAutoDraw(True)
#                     yield ()
#
#                 img.setAutoDraw(False)
#                 yield True
#                 yield True
#
#                 self.trials.addData("trial_ISI_start", self.task_timer.getTime())
#                 for frameN in range(int(config.FRAME_RATE * ISI_base / 2)):
#                     self.fixation.setAutoDraw(True)
#                     yield True
#                     yield True
#                     yield ()
#
#                 self.fixation.setAutoDraw(False)
#                 yield True
#                 yield True
#
#                 n_stim = 3
#                 img.image = IMAGES_FOLDER + "/" + str(trial["frame_obj_%s" % str(n_stim)]) + "/image.png"
#                 if self.feature != "loc":
#                     img.pos = (0, 0)
#                 else:
#                     img.pos = triplet_id_to_pos_ctxdm[trial["frame_loc_%s" % str(n_stim)]]
#
#                 for frameN in range(int(config.FRAME_RATE * STIMULI_DURATION/2)):
#                     img.setAutoDraw(True)
#                     yield True
#                     yield True
#                     yield ()
#
#                 img.setAutoDraw(False)
#                 self.fixation.setAutoDraw(False)
#                 yield True
#                 yield True
#
#                 self.trials.addData("trial_ISI_start", self.task_timer.getTime())
#                 for frameN in range(int(config.FRAME_RATE * ISI_base/2)):
#
#                     self.fixation.setAutoDraw(False)
#                     multfs_answer_keys = event.getKeys(
#                         [MULTFS_YES_KEY, MULTFS_NO_KEY, 'space', 'A', 'Y'], timeStamped=True
#                     )
#                     if len(multfs_answer_keys):
#                         self.trials.addData("response", multfs_answer_keys[-1][0])
#                         self.trials.addData("response_time", multfs_answer_keys[-1][1])
#                         self.trials.addData("response_time_2", self.task_timer.getTime())
#                     yield True
#                     yield True
#                     yield ()
#
#
#                 n_stim = 4
#                 img.image = IMAGES_FOLDER + "/" + str(trial["frame_obj_%s" % str(n_stim)]) + "/image.png"
#                 if self.feature != "loc":
#                     img.pos = (0, 0)
#                 else:
#                     img.pos = triplet_id_to_pos_ctxdm[trial["frame_loc_%s" % str(n_stim)]]
#
#                 for frameN in range(int(config.FRAME_RATE * STIMULI_DURATION/2)):
#                     img.setAutoDraw(True)
#                     yield True
#                     yield True
#                     yield ()
#
#                 img.setAutoDraw(False)
#                 self.fixation.setAutoDraw(False)
#                 yield True
#                 yield True
#
#                 self.trials.addData("trial_ISI_start", self.task_timer.getTime())
#                 for frameN in range(int(config.FRAME_RATE * ISI_base/2)):
#
#                     self.fixation.setAutoDraw(False)
#                     yield True
#                     yield True
#                     multfs_answer_keys = event.getKeys(
#                         [MULTFS_YES_KEY, MULTFS_NO_KEY, 'space', 'A', 'Y'], timeStamped=True
#                     )
#                     if len(multfs_answer_keys):
#                         self.trials.addData("response", multfs_answer_keys[-1][0])
#                         self.trials.addData("response_time", multfs_answer_keys[-1][1])
#                         self.trials.addData("response_time_2", self.task_timer.getTime())
#                         break
#
#                     yield ()
#
#                 img.setAutoDraw(False)
#                 self.fixation.setAutoDraw(False)
#                 yield True
#                 yield True
#                 for frameN in range(int(config.FRAME_RATE * ISI_base)):
#                     self.next_trial.draw()
#                     yield True
#                 for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
#                     self.empty_text.draw()
#                     yield True
#
#
#                 if trial_idx > 3:
#                     self.trials.addData("trial_end", self.task_timer.getTime())
#                     break
#
#             for clearBuffer in self._block_end(exp_win, ctl_win):
#                 self._flip_all_windows(exp_win, ctl_win, clearBuffer)
#             yield True
#             for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
#                 self.empty_text.draw()
#                 yield True
#     def _save(self):
#         self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
#         return False

# class multfs_interdms_ABBA(multfs_base):
#
#     def __init__(self, items_list, feature = "loc", session = None, **kwargs):
#         super().__init__(items_list, **kwargs)
#         self.feature = feature
#         self.pattern = "ABBA"
#         self.session = session # todo: add progress bar
#
#     def _run(self, exp_win, ctl_win):
#         self.trials = data.TrialHandler(self.item_list, 1, method="random")
#         exp_win.logOnFlip(
#             level=logging.EXP, msg="memory: task starting at %f" % time.time()
#         )
#         n_blocks = 2 # TODO: CHANGE THE NUMBER OF BLOCKS PER TASK VARIATION
#         for block in range(n_blocks):
#             for clearBuffer in self._block_intro(exp_win, ctl_win):
#                 self._flip_all_windows(exp_win, ctl_win, clearBuffer)
#             # 2 flips to clear screen
#             for i in range(2):
#                 yield True
#
#             img = visual.ImageStim(exp_win, size=STIMULI_SIZE, units="norm")
#
#             trial_idx = 0
#             for trial in self.trials:
#                 exp_win.logOnFlip(level=logging.EXP,
#                                   msg="multfs-interDMS_%s_%s: block %d " % (self.pattern, self.feature, block,))
#
#                 onset = self.task_timer.getTime()
#                 event.getKeys([MULTFS_YES_KEY, MULTFS_NO_KEY, "A", "Y"])
#
#                 trial_idx += 1
#                 for i in range(2):
#                     yield True
#
#                 # print("global time since the start of stim presentation:", self.task_timer.getTime())
#                 self.trials.addData("trial_stim_start",self.task_timer.getTime())
#
#                 n_stim = 1
#                 img.image = IMAGES_FOLDER + "/" + str(trial["frame_obj_%s" % str(n_stim)]) + "/image.png"
#                 if self.feature != "loc":
#                     img.pos = (0, 0)
#                 else:
#                     img.pos = triplet_id_to_pos_ctxdm[trial["frame_loc_%s" % str(n_stim)]]
#
#                 for frameN in range(int(config.FRAME_RATE * STIMULI_DURATION/2)):
#                     yield True
#                     yield True
#                     img.setAutoDraw(True)
#                     self.fixation.setAutoDraw(True)
#                     yield()
#
#
#                 img.setAutoDraw(False)
#                 yield True
#                 yield True
#
#
#                 self.trials.addData("trial_ISI_start", self.task_timer.getTime())
#                 for frameN in range(int(config.FRAME_RATE * ISI_base/2)):
#                     self.fixation.setAutoDraw(True)
#                     yield True
#                     yield True
#                     yield ()
#
#                 self.fixation.setAutoDraw(False)
#                 yield True
#                 yield True
#
#                 n_stim = 2
#                 img.image = IMAGES_FOLDER + "/" + str(trial["frame_obj_%s" % str(n_stim)]) + "/image.png"
#                 if self.feature != "loc":
#                     img.pos = (0, 0)
#                 else:
#                     img.pos = triplet_id_to_pos_ctxdm[trial["frame_loc_%s" % str(n_stim)]]
#
#                 for frameN in range(int(config.FRAME_RATE * STIMULI_DURATION / 2)):
#                     yield True
#                     yield True
#                     img.setAutoDraw(True)
#                     self.fixation.setAutoDraw(True)
#                     yield ()
#
#                 img.setAutoDraw(False)
#                 yield True
#                 yield True
#
#                 self.trials.addData("trial_ISI_start", self.task_timer.getTime())
#                 for frameN in range(int(config.FRAME_RATE * ISI_base / 2)):
#                     self.fixation.setAutoDraw(True)
#                     yield True
#                     yield True
#                     yield ()
#
#                 self.fixation.setAutoDraw(False)
#                 yield True
#                 yield True
#
#                 n_stim = 3
#                 img.image = IMAGES_FOLDER + "/" + str(trial["frame_obj_%s" % str(n_stim)]) + "/image.png"
#                 if self.feature != "loc":
#                     img.pos = (0, 0)
#                 else:
#                     img.pos = triplet_id_to_pos_ctxdm[trial["frame_loc_%s" % str(n_stim)]]
#
#                 for frameN in range(int(config.FRAME_RATE * STIMULI_DURATION/2)):
#                     img.setAutoDraw(True)
#                     yield True
#                     yield True
#                     yield ()
#
#                 img.setAutoDraw(False)
#                 self.fixation.setAutoDraw(False)
#                 yield True
#                 yield True
#
#                 self.trials.addData("trial_ISI_start", self.task_timer.getTime())
#                 for frameN in range(int(config.FRAME_RATE * ISI_base/2)):
#
#                     self.fixation.setAutoDraw(False)
#                     multfs_answer_keys = event.getKeys(
#                         [MULTFS_YES_KEY, MULTFS_NO_KEY, 'space', 'A', 'Y'], timeStamped=True
#                     )
#                     if len(multfs_answer_keys):
#                         self.trials.addData("response", multfs_answer_keys[-1][0])
#                         self.trials.addData("response_time", multfs_answer_keys[-1][1])
#                         self.trials.addData("response_time_2", self.task_timer.getTime())
#                     yield True
#                     yield True
#                     yield ()
#
#
#                 n_stim = 4
#                 img.image = IMAGES_FOLDER + "/" + str(trial["frame_obj_%s" % str(n_stim)]) + "/image.png"
#                 if self.feature != "loc":
#                     img.pos = (0, 0)
#                 else:
#                     img.pos = triplet_id_to_pos_ctxdm[trial["frame_loc_%s" % str(n_stim)]]
#
#                 for frameN in range(int(config.FRAME_RATE * STIMULI_DURATION/2)):
#                     img.setAutoDraw(True)
#                     yield True
#                     yield True
#                     yield ()
#
#                 img.setAutoDraw(False)
#                 self.fixation.setAutoDraw(False)
#                 yield True
#                 yield True
#
#                 self.trials.addData("trial_ISI_start", self.task_timer.getTime())
#                 for frameN in range(int(config.FRAME_RATE * ISI_base/2)):
#
#                     self.fixation.setAutoDraw(False)
#                     yield True
#                     yield True
#                     multfs_answer_keys = event.getKeys(
#                         [MULTFS_YES_KEY, MULTFS_NO_KEY, 'space', 'A', 'Y'], timeStamped=True
#                     )
#                     if len(multfs_answer_keys):
#                         self.trials.addData("response", multfs_answer_keys[-1][0])
#                         self.trials.addData("response_time", multfs_answer_keys[-1][1])
#                         self.trials.addData("response_time_2", self.task_timer.getTime())
#                         break
#
#                     yield ()
#
#                 img.setAutoDraw(False)
#                 self.fixation.setAutoDraw(False)
#                 yield True
#                 yield True
#                 for frameN in range(int(config.FRAME_RATE * ISI_base)):
#                     self.next_trial.draw()
#                     yield True
#                 for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
#                     self.empty_text.draw()
#                     yield True
#
#
#                 if trial_idx > 3:
#                     self.trials.addData("trial_end", self.task_timer.getTime())
#                     break
#
#             for clearBuffer in self._block_end(exp_win, ctl_win):
#                 self._flip_all_windows(exp_win, ctl_win, clearBuffer)
#             yield True
#             for frameN in range(int(config.FRAME_RATE * ISI_base / 4)):
#                 self.empty_text.draw()
#                 yield True
#     def _save(self):
#         self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
#         return Fals

def instructions_converter(task_name):
    task = task_name[5:].split('_run')[0]
    task = f"multfs_{task}"

    ins_dict = {
        "multfs_dmsloc": """Press X if two stimulus are at the same location, otherwise press B/\n
Press A to continue""",

        "multfs_interdmsloc_ABBA": """
interleaved Delay match to sample task with pattern ABBA and feature location\n
Press X on the fourth frame if the first and fourth stimuli have the same location,  otherwise press B.\n
Press X on the third frame if the second and third stimuli have the same location,  otherwise press B.\n
Press A to continue
                              """,
        "multfs_interdmscat_ABBA": """
interleaved Delay match to sample task with pattern ABBA and feature category\n
  Press X on the fourth frame if the first and fourth stimuli have the same category,  otherwise press B.\n
  Press X on the third frame if the second and third stimuli have the same category,  otherwise press B.\n
  Press A to continue
                                  """,
        "multfs_interdmsobj_ABBA": """
interleaved Delay match to sample task with pattern ABBA and feature object\n
  Press X on the fourth frame if the first and fourth stimuli are the same object,  otherwise press B.\n
  Press X on the third frame if the third and third stimuli are the same object,  otherwise press B.\n
  Press A to continue
                                  """,
        "multfs_interdmsloc_ABAB": """
interleaved Delay match to sample task with pattern ABAB and feature location\n
  Press X on the third frame if the first and third stimuli have the same location,  otherwise press B.\n
  Press X on the fourth frame if the second and fourth stimuli have the same location,  otherwise press B.\n
  Press A to continue
                              """,
        "multfs_interdmscat_ABAB": """
interleaved Delay match to sample task with pattern ABAB and feature category\n
  Press X on the third frame if the first and third stimuli have the same category,  otherwise press B.\n
  Press X on the fourth frame if the second and fourth stimuli have the same category,  otherwise press B.\n
  Press A to continue
                                  """,
        "multfs_interdmsobj_ABAB": """
interleaved Delay match to sample task with pattern ABAB and feature object\n
  Press X on the third frame if the first and third stimuli are the same object,  otherwise press B.\n
  Press X on the fourth frame if the second and fourth stimuli are the same object,  otherwise press B.\n
  Press A to continue
                                  """,
        "multfs_1backloc": """
In this task, you will see a sequence of stimulus presented one after another.\n
Press X each time the current stimulus is at the same location as the one presented just before. \n
Otherwise press B\n
Press A to continue
                    """,
        "multfs_1backobj": """
In this task, you will see a sequence of stimulus presented one after another. \n
Press X each time the current stimulus is the same object as the one presented just before. \n
Otherwise press B \n
Press A to continue
                    """,
        "multfs_1backcat": """
In this task, you will see a sequence of stimulus presented one after another.\n
Press X each time the current stimulus belong to the same category as the one presented just before.\n
Otherwise press B \n
Press A to continue
                    """,

        "multfs_ctxcol": """
If the presented two stimuli belong to the same category, press X if they are the same object, press B if not.\n
If the presented two stimuli does not belong to the same category, press X if they are at the same location, press B if not.\n
Press A to continue
                        """,
        "multfs_ctxlco": """
contextual Decision Making task: location-category-object \n
If the presented two stimuli are at the same location, press X if they belong to the same category, press B if not.\n
If the presented two stimuli are not at the same location, press X if they are same object, press B if not.\n
Press A to continue
                    """,
    }
    return ins_dict[task]


def abbrev_instructions_converter(task_name):
    task = task_name[5:].split('_run')[0]
    task = f"multfs_{task}"

    ins_dict = {
        "multfs_dmsloc": "DMS-LOCATION",

        "multfs_interdmsloc_ABBA": """interDMS-ABBA-LOCATION\n
                              """,
        "multfs_interdmscat_ABBA": """interDMS-ABBA-CATEGORY\n
                                  """,
        "multfs_interdmsobj_ABBA": """interDMS-ABBA-IDENTITY\n
                                  """,
        "multfs_interdmsloc_ABAB": """interDMS-ABAB-LOCATION\n
                              """,
        "multfs_interdmscat_ABAB": """interDMS-ABAB-CATEGORY\n
                                  """,
        "multfs_interdmsobj_ABAB": """interDMS-ABAB-IDENTITY\n
                                  """,
        "multfs_1backloc": """1back-LOCATION\n
                    """,
        "multfs_1backobj": """1back-IDENTITY\n
                    """,
        "multfs_1backcat": """1back-CATEGORY\n
                    """,

        "multfs_ctxcol": """ctxDM-CATEGORY-IDENTITY-LOCATION\n
                        """,
        "multfs_ctxlco": """ctxDM-LOCATION-CATEGORY-IDENTITY\n
                    """,
    }
    return ins_dict[task]
