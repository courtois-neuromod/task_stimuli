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

STIMULI_DURATION = 0.75
ISI_base = 2
nback_ISI_base = 2
short_ISI_base = 0.5
IMAGES_FOLDER = "data/multfs/MULTIF_4_stim"


MULTFS_YES_KEY = "x"
MULTFS_NO_KEY = "b"
CONTINUE_KEY = "a"

config.INSTRUCTION_DURATION = 2

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

        self._trial_sampling_method = "random"

    def _setup(self, exp_win):
        self.fixation = visual.TextStim(exp_win, text="+", alignText="center", color="white")
        self.next_trial = visual.TextStim(exp_win, text="Next trial!", alignText = "center", color = "white", height = 0.1)
        self.empty_text = visual.TextStim(exp_win, text="", alignText = "center", color = "white", height = 0.1)
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
        for frameN in range(int(np.floor(config.FRAME_RATE * config.INSTRUCTION_DURATION))):
            screen_text_bold.draw(exp_win)
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text_bold.draw(ctl_win)
                screen_text.draw(ctl_win)

            # keys = psychopy.event.getKeys(keyList=['space','a'])
            # if keys:
            #     resp_time = self.globalClock.getTime()
            #     # print("end of the instruction time:", resp_time) # todo: record response time for reading instructions [an empty dict in the init?]
            #     if keys[-1] == "space" or 'a':
            #         break
            yield ()
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
        self.fixation.draw()
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
        self.fixation.draw()
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
        self.trials = data.TrialHandler(self.item_list, 1, method=self._trial_sampling_method)
        exp_win.logOnFlip(
            level=logging.EXP, msg=f"memory: {self.name} starting"
        )
        n_blocks = self.n_blocks # TODO: CHANGE THE NUMBER OF BLOCKS PER TASK VARIATION

        img = visual.ImageStim(exp_win, size=STIMULI_SIZE, units="norm")

        for block in range(n_blocks):
            onset = (
                initial_wait +
                (block) * config.INSTRUCTION_DURATION +
                (block * self.n_trials) * ( self.seq_len * (STIMULI_DURATION+ISI_base/4) + ISI_base * 6./4)
                )
            yield from self._block_intro(exp_win, ctl_win, onset, self.n_trials)

            trial_idx = 0
            for trial in self.trials:
                exp_win.logOnFlip(level=logging.EXP, msg=f"{self.name}_{self.feature}: block {block} trial {trial_idx}")
                trial_idx += 1

                for n_stim in range(self.seq_len):

                    onset = (
                        initial_wait +
                        (block + 1) * config.INSTRUCTION_DURATION +
                        (block * self.n_trials + (trial_idx-1)) * ( self.seq_len * (STIMULI_DURATION+ISI_base/4) + ISI_base * 6/4) +
                        n_stim*(STIMULI_DURATION+ISI_base/4))
                    print(onset)

                    img.image = IMAGES_FOLDER + "/" + str(trial["objmod%s" % str(n_stim+1)]) + "/image.png"
                    img.pos = triplet_id_to_pos[trial[f"loc{n_stim+1}"]]
                    img.draw()

                    utils.wait_until(self.task_timer, onset - 1/config.FRAME_RATE)
                    yield True
                    self.trials.addData(
                        "stimulus_%d_onset" % n_stim,
                        self._exp_win_last_flip_time - self._exp_win_first_flip_time)
                    utils.wait_until(self.task_timer, onset + STIMULI_DURATION - 1/config.FRAME_RATE)
                    yield True
                    self.trials.addData(
                        "stimulus_%d_offset" % n_stim,
                        self._exp_win_last_flip_time - self._exp_win_first_flip_time)

                    multfs_answer_keys = psychopy.event.getKeys(
                        [MULTFS_YES_KEY, MULTFS_NO_KEY, 'space'], timeStamped=self.task_timer
                    )

                    if len(multfs_answer_keys):
                        self.trials.addData("response_%d" % n_stim, multfs_answer_keys[-1][0])
                        self.trials.addData("response_%d_time" % n_stim, multfs_answer_keys[-1][1])
                        self.trials.addData("all_responses" % n_stim, multfs_answer_keys)

                self.fixation.draw()
                utils.wait_until(self.task_timer, onset + STIMULI_DURATION + ISI_base - 1./config.FRAME_RATE)
                yield True
                utils.wait_until(self.task_timer, onset + STIMULI_DURATION + ISI_base * 5/4. - 1./config.FRAME_RATE)
                yield True


                if trial_idx >= self.n_trials:
                    self.trials.addData("trial_end", self.task_timer.getTime())
                    break

            yield from self._block_end(exp_win, ctl_win, onset + STIMULI_DURATION + ISI_base * 6/4. - 1./config.FRAME_RATE)


class multfs_dms(multfs_base):

    def __init__(self, items_list, feature = "loc", session = None, **kwargs):
        super().__init__(items_list, **kwargs)
        if "subtraining" in items_list:
            self.n_trials = 4
            self.n_blocks = 2
        else:
            self.n_trials = 8 # todo to be modified to in accordance with the file => this is fine as the baseline task
            self.n_blocks = 2

        self.feature = feature
        self.session = session # todo: add progress bar

        self.seq_len = 2

        self._trial_sampling_method = "sequential" # why sequential here, to figure out with Xiaoxuan


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
            self.n_trials = 10
            self.n_blocks = 1 # around 7 mins

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
            self.n_trials = 22
            self.n_blocks = 1


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


def instructions_converter(task_name):
    task = task_name[5:].split('_run')[0]
    task = f"multfs_{task}"

    ins_dict = {
        "multfs_dmsloc": """Press X if two stimulus are at the same location, otherwise press B/\n""",

        "multfs_interdmsloc_ABBA": """
interleaved Delay match to sample task with pattern ABBA and feature location\n
Press X on the fourth frame if the first and fourth stimuli have the same location,  otherwise press B.\n
Press X on the third frame if the second and third stimuli have the same location,  otherwise press B.\n
                              """,
        "multfs_interdmscat_ABBA": """
interleaved Delay match to sample task with pattern ABBA and feature category\n
  Press X on the fourth frame if the first and fourth stimuli have the same category,  otherwise press B.\n
  Press X on the third frame if the second and third stimuli have the same category,  otherwise press B.\n

                                  """,
        "multfs_interdmsobj_ABBA": """
interleaved Delay match to sample task with pattern ABBA and feature object\n
  Press X on the fourth frame if the first and fourth stimuli are the same object,  otherwise press B.\n
  Press X on the third frame if the third and third stimuli are the same object,  otherwise press B.\n

                                  """,
        "multfs_interdmsloc_ABAB": """
interleaved Delay match to sample task with pattern ABAB and feature location\n
  Press X on the third frame if the first and third stimuli have the same location,  otherwise press B.\n
  Press X on the fourth frame if the second and fourth stimuli have the same location,  otherwise press B.\n

                              """,
        "multfs_interdmscat_ABAB": """
interleaved Delay match to sample task with pattern ABAB and feature category\n
  Press X on the third frame if the first and third stimuli have the same category,  otherwise press B.\n
  Press X on the fourth frame if the second and fourth stimuli have the same category,  otherwise press B.\n

                                  """,
        "multfs_interdmsobj_ABAB": """
interleaved Delay match to sample task with pattern ABAB and feature object\n
  Press X on the third frame if the first and third stimuli are the same object,  otherwise press B.\n
  Press X on the fourth frame if the second and fourth stimuli are the same object,  otherwise press B.\n

                                  """,
        "multfs_1backloc": """
In this task, you will see a sequence of stimulus presented one after another.\n
Press X each time the current stimulus is at the same location as the one presented just before. \n
Otherwise press B\n
                    """,
        "multfs_1backobj": """
In this task, you will see a sequence of stimulus presented one after another. \n
Press X each time the current stimulus is the same object as the one presented just before. \n
Otherwise press B \n
                    """,
        "multfs_1backcat": """
In this task, you will see a sequence of stimulus presented one after another.\n
Press X each time the current stimulus belong to the same category as the one presented just before.\n
Otherwise press B \n
                    """,

        "multfs_ctxcol": """
If the presented two stimuli belong to the same category, press X if they are the same object, press B if not.\n
If the presented two stimuli does not belong to the same category, press X if they are at the same location, press B if not.\n
                        """,
        "multfs_ctxlco": """
contextual Decision Making task: location-category-object \n
If the presented two stimuli are at the same location, press X if they belong to the same category, press B if not.\n
If the presented two stimuli are not at the same location, press X if they are same object, press B if not.\n
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
