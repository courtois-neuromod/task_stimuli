import os, sys, time, random
import numpy as np
import psychopy
from psychopy import visual, core, data, logging, event
from psychopy.hardware import keyboard
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED, STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)
from .task_base import Task
from .task_base import Fixation
#psychopy.useVersion('latest')

from ..shared import config, utils

initial_wait = 6
final_wait = 9

TR = 1.49
STIMULI_DURATION = TR
ISI_base = 2 * TR + 1
long_ISI_base = 2 * TR + 1
short_ISI_base = 0.5
IMAGES_FOLDER = "data/multfs/MULTIF_4_stim"


MULTFS_YES_KEY = "x"
MULTFS_NO_KEY = "b"
CONTINUE_KEY = "a"

INSTRUCTION_DURATION = 120

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
        self.instruction = instructions_converter(self.name) + "\n" + INSTRUCTIONS_DONE
        self.abbrev_instruction = abbrev_instructions_converter(self.name)
        # print("abbrev instruction:", self.abbrev_instruction)
        self.globalClock = core.Clock() # to track the time since experiment start
        self.routineTimer = core.Clock() # to track time remaining of each (possibly non-slip) routine
        self.frameTolerance = 0.001 # how close to onset before 'same' frame
        self.storage_dict = {}

        self._trial_sampling_method = "random"

    def _setup(self, exp_win):
        self.fixation = visual.TextStim(exp_win, text="+", alignText="center", color="white")
        self.empty_text = visual.TextStim(exp_win, text="", alignText = "center", color = "white", height = 0.1)
        self.no_response_marker = visual.Circle(exp_win, 20, units='pix', fillColor=(255,0,0), fillColorSpace='rgb255')

        total_duration = (
            initial_wait +
            (self.n_blocks * self.n_trials) *
            ( self.seq_len * STIMULI_DURATION + sum(self.trial_isis) ) +
            final_wait
            )
        print(f"TOTAL DURATION: {total_duration}")

        super()._setup(exp_win)

    def _instructions(self, exp_win, ctl_win):
        yield True
        if ctl_win:
            win = ctl_win
        else:
            win = exp_win
        screen_text_bold = visual.TextStim(
            win=exp_win,
            name='introtext_bold',
            text=self.abbrev_instruction,
            font='Arial',
            pos=(0, 0.5), height=0.1, ori=0,
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
        for frameN in range(int(np.floor(config.FRAME_RATE * INSTRUCTION_DURATION))):
            screen_text_bold.draw(exp_win)
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text_bold.draw(ctl_win)
                screen_text.draw(ctl_win)

            keys = psychopy.event.getKeys(keyList=['space','a'])
            if keys:
                break
            # keys = psychopy.event.getKeys(keyList=['space','a'])
            # if keys:
            #     resp_time = self.globalClock.getTime()
            #     # print("end of the instruction time:", resp_time) # todo: record response time for reading instructions [an empty dict in the init?]
            #     if keys[-1] == "space" or 'a':
            #         break
            yield False
        # print("end of the instruction time:", resp_time)

    def _block_intro(self, exp_win, ctl_win, onset, n_trials = 4):
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
            text= 'New Block! \n\nEach block contains %d trials, each starts with fixation. \n\nWait to continue!' % n_trials, # todo: modify the key instructions
            font='Open Sans',
            pos=(0, 0), height=0.05, ori=0,
            color="white", colorSpace='rgb', opacity=1,
            languageStyle='LTR',
            wrapWidth=config.WRAP_WIDTH,
        )

        # -- prepare to start Routine "Intro" --
        print("start of the block instruction:", self.globalClock.getTime())
        screen_text_bold.draw(exp_win)
        screen_text.draw(exp_win)
        if ctl_win:
            screen_text_bold.draw(ctl_win)
            screen_text.draw(ctl_win)
        utils.wait_until(self.task_timer, onset - 1./config.FRAME_RATE)
        yield True
        utils.wait_until(
            self.task_timer,
            onset + config.INSTRUCTION_DURATION - 10./config.FRAME_RATE
        )
        yield True
        psychopy.event.getKeys() # flush keys ?
        print("end of the block instruction:", self.globalClock.getTime())


    def _block_end(self, exp_win, ctl_win, onset):
        if ctl_win:
            win = ctl_win
        else:
            win = exp_win
        screen_text = visual.TextStim(
            win=exp_win,
            name='blockendtext',
            text= 'End of the block! \n\nWait to start next block', # todo: modify the key instructions
            font='Open Sans',
            pos=(0, 0), height=0.05, ori=0,
            color="white", colorSpace='rgb', opacity=1,
            languageStyle='LTR',
            wrapWidth=config.WRAP_WIDTH,
        )
        utils.wait_until(self.task_timer, onset - 1./config.FRAME_RATE)
        # -- prepare to start Routine "Intro" --
        screen_text.draw(exp_win)
        if ctl_win:
            screen_text.draw(ctl_win)
        yield True
        utils.wait_until(
            self.task_timer,
            onset + config.INSTRUCTION_DURATION - 10./config.FRAME_RATE
        )
        yield True

    def _save(self):
        if hasattr(self, 'trials'):
            self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
        return None


    def _run(self, exp_win, ctl_win):
        self.fixation.draw()
        yield True
        self.trials = data.TrialHandler(self.item_list, 1, method=self._trial_sampling_method)
        exp_win.logOnFlip(
            level=logging.EXP, msg=f"memory: {self.name} starting"
        )
        n_blocks = self.n_blocks # TODO: CHANGE THE NUMBER OF BLOCKS PER TASK VARIATION

        img = visual.ImageStim(exp_win, size=STIMULI_SIZE, units="norm")

        for block in range(n_blocks):
            onset = (
                initial_wait +
                #(block) * config.INSTRUCTION_DURATION +
                (block * self.n_trials) * ( self.seq_len * STIMULI_DURATION + sum(self.trial_isis))
                )
            #yield from self._block_intro(exp_win, ctl_win, onset, self.n_trials)

            trial_idx = 0
            for trial in self.trials:
                exp_win.logOnFlip(level=logging.EXP, msg=f"{self.name}_{self.feature}: block {block} trial {trial_idx}")
                trial_idx += 1

                for n_stim in range(self.seq_len):

                    onset = (
                        initial_wait +
                        #(block + 1) * config.INSTRUCTION_DURATION +
                        (block * self.n_trials + (trial_idx-1)) *
                        ( self.seq_len * STIMULI_DURATION + sum(self.trial_isis)) +
                        n_stim*STIMULI_DURATION + sum(self.trial_isis[:n_stim])
                        )

                    img.image = IMAGES_FOLDER + "/" + str(trial["ref%s" % str(n_stim+1)]) + "/image.png"
                    if not 'interdms' in self.name:
                        img.pos = triplet_id_to_pos[trial[f"loc{n_stim+1}"]]
                    else:
                        img.pos = triplet_id_to_pos[trial[f"locmod{n_stim+1}"]]
                    img.draw()

                    # flush response keys before the stimuli onset
                    multfs_answer_keys = psychopy.event.getKeys([MULTFS_YES_KEY, MULTFS_NO_KEY, 'space'])
                    # log responses leaking from the previous trial, in case we want to exclude corrupted trial
                    self.trials.addData("late_responses_%d" % n_stim, multfs_answer_keys)

                    if n_stim in self.no_response_frames:
                        self.no_response_marker.draw(exp_win)

                    utils.wait_until(self.task_timer, onset - 1/config.FRAME_RATE)
                    yield True
                    self.trials.addData(
                        "stimulus_%d_onset" % n_stim,
                        self._exp_win_last_flip_time - self._exp_win_first_flip_time)
                    utils.wait_until(
                        self.task_timer,
                        onset + STIMULI_DURATION - 1/config.FRAME_RATE,
                        keyboard_accuracy=.0001)
                    # draw fixation for ITI
                    if n_stim == self.seq_len-1:
                        self.fixation.draw()
                    yield True
                    self.trials.addData(
                        "stimulus_%d_offset" % n_stim,
                        self._exp_win_last_flip_time - self._exp_win_first_flip_time)

                    # wait until almost the end of the ISI to collect responses.
                    utils.wait_until(
                        self.task_timer,
                        onset + STIMULI_DURATION + self.trial_isis[n_stim] - 10./config.FRAME_RATE,
                        keyboard_accuracy=.0001)

                    multfs_answer_keys = psychopy.event.getKeys(
                        [MULTFS_YES_KEY, MULTFS_NO_KEY, 'space'], timeStamped=self.task_timer
                    )

                    if n_stim not in self.no_response_frames:
                        if len(multfs_answer_keys):
                            self.trials.addData("response_%d" % n_stim, multfs_answer_keys[-1][0])
                            self.trials.addData("response_%d_time" % n_stim, multfs_answer_keys[-1][1])
                            self.trials.addData("all_responses_%d" % n_stim, multfs_answer_keys)


                utils.wait_until(self.task_timer, onset + STIMULI_DURATION + self.trial_isis[-1] - 9./config.FRAME_RATE)
                yield True

                if trial_idx >= self.n_trials:
                    self.trials.addData("trial_end", self.task_timer.getTime())
                    break

            #yield from self._block_end(exp_win, ctl_win, onset + STIMULI_DURATION + ISI_base * 6/4. - 1./config.FRAME_RATE)
        self.fixation.draw()
        yield True
        baseline_offset = onset + STIMULI_DURATION + self.trial_isis[-1] + final_wait
        print(f"baseline_offset {baseline_offset}")
        utils.wait_until(
            self.task_timer,
            baseline_offset - 1./config.FRAME_RATE)
        yield True


class multfs_dms(multfs_base):

    def __init__(self, items_list, feature = "loc", session = None, **kwargs):
        super().__init__(items_list, **kwargs)
        if "subtraining" in items_list:
            self.n_trials = 4
            self.n_blocks = 2
        else:
            self.n_trials = 16 # todo to be modified to in accordance with the file => this is fine as the baseline task
            self.n_blocks = 1

        self.feature = feature
        self.session = session # todo: add progress bar

        self.seq_len = 2
        self.no_response_frames = [0]
        self.trial_isis = [long_ISI_base, long_ISI_base]


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
            self.n_trials = 9
            self.n_blocks = 1 # around 7 mins
        self.no_response_frames = [0]
        self.trial_isis = [short_ISI_base] + [long_ISI_base] * 5


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
            self.n_trials = 20
            self.n_blocks = 1
        self.no_response_frames = [0, 1]
        self.trial_isis = [short_ISI_base, long_ISI_base, long_ISI_base]


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
            self.n_trials = 16
            self.n_blocks = 1
        self.no_response_frames = [0, 1]
        self.trial_isis = [short_ISI_base, long_ISI_base, long_ISI_base, long_ISI_base]


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
            self.n_trials = 16
            self.n_blocks = 1
        self.no_response_frames = [0, 1]
        self.trial_isis = [short_ISI_base, long_ISI_base, long_ISI_base, long_ISI_base]


INSTRUCTIONS_DONE = """X = yes
B = no \n\n
When ready press A.
"""

def instructions_converter(task_name):
    task = task_name[5:].split('_run')[0]
    task = f"multfs_{task}"

    ins_dict = {
        "multfs_dmsloc": """Do frame 1 and 2 have same LOCATION.\n""",

        "multfs_dmsobj": """Do frame 1 and 2 have same IDENTITY.\n""",

        "multfs_interdmslocABBA": """
interleaved delay match to sample task with pattern ABBA and feature LOCATION\n
Answer on frame 3: does the LOCATION match that of frame 2. \n
Answer on frame 4: does the LOCATION match that of frame 1. \n
                              """,
        "multfs_interdmsctgABBA": """
interleaved delay match to sample task with pattern ABBA and feature CATEGORY\n
Answer on frame 3: does the CATEGORY match that of frame 2. \n
Answer on frame 4: does the CATEGORY match that of frame 1. \n
                                  """,
        "multfs_interdmsobjABBA": """
interleaved delay match to sample task with pattern ABBA and feature IDENTITY\n
Answer on frame 3: does the IDENTITY match that of frame 2. \n
Answer on frame 4: does the IDENTITY match that of frame 1. \n
                                  """,
        "multfs_interdmslocABAB": """
interleaved delay match to sample task with pattern ABAB and feature LOCATION\n
Answer on frame 3: does the LOCATION match that of frame 1. \n
Answer on frame 4: does the LOCATION match that of frame 2. \n
                              """,
        "multfs_interdmsctgABAB": """
interleaved delay match to sample task with pattern ABAB and feature CATEGORY\n
Answer on frame 3: does the CATEGORY match that of frame 1. \n
Answer on frame 4: does the CATEGORY match that of frame 2. \n
                                  """,
        "multfs_interdmsobjABAB": """
interleaved delay match to sample task with pattern ABAB and feature IDENTITY\n
Answer on frame 3: does the IDENTITY match that of frame 1. \n
Answer on frame 4: does the IDENTITY match that of frame 2. \n
    """,
        "multfs_1backloc": """
In this task, you will see a sequence of stimulus.\n

On frame n+1: do the LOCATION match that of frame n.\n
                    """,
        "multfs_1backobj": """
In this task, you will see a sequence of stimulus. \n

On frame n+1: do the IDENTITY match that of frame n.\n

                    """,
        "multfs_1backctg": """
On frame n+1: do the CATEGORY match that of frame n.\n
""",

        "multfs_ctxcol": """
        contextual Decision Making task: CATEGORY-IDENTITY-LOCATION \n
        If frames 1 and 2 match on CATEGORY, match frames 2 and 3 based on IDENTITY, otherwise on LOCATION.\n
                """,
        "multfs_ctxlco": """
contextual Decision Making task: LOCATION-CATEGORY-IDENTITY \n
If frames 1 and 2 match on LOCATION, match frames 2 and 3 based on CATEGORY, otherwise on IDENTITY.\n
                    """,
    }
    return ins_dict[task]


def abbrev_instructions_converter(task_name):
    task = task_name[5:].split('_run')[0]
    task = f"multfs_{task}"

    ins_dict = {
        "multfs_dmsloc": "DMS-LOCATION",

        "multfs_dmsobj": "DMS-IDENTITY",

        "multfs_interdmslocABBA": """interDMS-ABBA-LOCATION\n
                              """,
        "multfs_interdmsctgABBA": """interDMS-ABBA-CATEGORY\n
                                  """,
        "multfs_interdmsobjABBA": """interDMS-ABBA-IDENTITY\n
                                  """,
        "multfs_interdmslocABAB": """interDMS-ABAB-LOCATION\n
                              """,
        "multfs_interdmsctgABAB": """interDMS-ABAB-CATEGORY\n
                                  """,
        "multfs_interdmsobjABAB": """interDMS-ABAB-IDENTITY\n
                                  """,
        "multfs_1backloc": """1back-LOCATION\n
                    """,
        "multfs_1backobj": """1back-IDENTITY\n
                    """,
        "multfs_1backctg": """1back-CATEGORY\n
                    """,

        "multfs_ctxcol": """ctxDM-CATEGORY-IDENTITY-LOCATION\n
                        """,
        "multfs_ctxlco": """ctxDM-LOCATION-CATEGORY-IDENTITY\n
                    """,
    }
    return ins_dict[task]
