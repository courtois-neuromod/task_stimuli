import os, sys, time
import os.path as op
import numpy as np
from glob import glob
from psychopy import visual, core, data, logging, event
from pandas import DataFrame, read_csv
from .task_base import Task
import json

from ..shared import config, utils

STIMULI_DURATION = 4
BASELINE_BEGIN = 5
BASELINE_END = 5
ISI = 2


### Adapted from https://github.com/NBCLab/pyfLoc
### to fit in our acquisition scheme

class FLoc(Task):

    DEFAULT_INSTRUCTION = """You will be presented a text to read word by word."""
    RESPONSE_KEYS = ['a']

    def __init__(self, task, images_sets, *args, **kwargs):
        super().__init__(**kwargs)
        self.task = task
        self.images_sets = images_sets

    def _instructions(self, exp_win, ctl_win):


        if self.task == 'Oddball':
            instruction_text = 'Fixate. Press a button when a scrambled image appears.'
        elif self.task == 'TwoBack':
            instruction_text = 'Fixate. Press a button when an image repeats with one intervening image.'
        else:
            instruction_text = 'Fixate. Press a button when an image repeats on sequential trials.'

        screen_text = visual.TextStim(
            exp_win,
            text=instruction_text,
            alignText="center",
            wrapWidth=1.2,
        )

        for frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield ()

    def _setup(self, exp_win):


        config_file = op.join('data/fLoc', 'config.json')
        with open(config_file, 'r') as fo:
            self.config = json.load(fo)
        self.constants = self.config['constants']
        self.constants['TRIAL_DURATION'] = self.constants['IMAGE_DURATION'] + self.constants['TARGET_ISI']

        self.stim_image = visual.ImageStim(
            win=exp_win,
            name='stimulus',
            image=None,
            ori=0,
            pos=(0, 0),
            size=(768, 768),
            units='pixels',
            color=[1, 1, 1],
            colorSpace='rgb',
            opacity=1,
            depth=-1.0,
            interpolate=False)
        self.fixation = visual.TextStim(
            win=exp_win,
            name='fixation',
            text=u'\u2022',
            font=u'Arial',
            pos=(0, 0),
            height=30,
            units='pixels',
            wrapWidth=None,
            ori=0,
            color='red',
            colorSpace='rgb',
            opacity=1,
            depth=0.0)


        stimulus_folders = self.config["category_sets"][self.images_sets]

        standard_categories = [cat for cat in stimulus_folders.keys() if cat != 'scrambled']
        n_categories = len(standard_categories)
        n_blocks_per_category = int(np.floor(self.constants['N_BLOCKS'] / n_categories))

        self.stimuli = {}
        for category in stimulus_folders.keys():
            if stimulus_folders[category] is not None:
                stimulus_files = [glob(op.join('data','fLoc', 'stimuli/{}/*.jpg'.format(stimulus_folder))) for
                                  stimulus_folder in stimulus_folders[category]]
                # Unravel list of lists
                stimulus_files = [item for sublist in stimulus_files for item in sublist]
                # Clean up paths
                stimulus_files = [op.realpath(item).replace('\\', '/') for item in stimulus_files]
                self.stimuli[category] = stimulus_files
            else:
                self.stimuli[category] = None  # baseline trials just have fixation

        self._progress_bar_refresh_rate = 1 # 1 flip / trial

        # Determine which trials will be task
        # This might be overly convoluted, but it maximizes balance between
        # task/non-task instead of just sampling with set probabilities
        nontask_rate = 1 - self.constants['TASK_RATE']
        task_mult = 1 / np.minimum(self.constants['TASK_RATE'], nontask_rate)
        n_task_prop = int(task_mult * self.constants['TASK_RATE'])
        n_nontask_prop = int(task_mult * nontask_rate)
        grabber_list = [1] * n_task_prop + [0] * n_nontask_prop

        # We want to ensure that tasks are not assigned to baseline blocks
        n_nonbaseline_blocks = int(self.constants['N_BLOCKS'] * (n_categories - 1) / n_categories)
        n_dupes = int(np.ceil(n_nonbaseline_blocks / len(grabber_list)))
        self.task_miniblocks = grabber_list * n_dupes

        self.miniblock_categories = randomize_carefully(standard_categories, n_blocks_per_category)
        np.random.shuffle(self.task_miniblocks)

        self.duration = self.constants['TOTAL_DURATION']
        self._progress_bar_refresh_rate = 2

    def _run(self, exp_win, ctl_win):
        exp_win.logOnFlip(
            level=logging.EXP, msg="fLoc: task starting at %f" % time.time()
        )
        self.fixation.draw(exp_win)
        yield True
        utils.wait_until(self.task_timer, self.constants['COUNTDOWN_DURATION'])

        run_responses, run_response_times = [], []
        nonbaseline_block_counter = 0
        block_duration = self.constants['N_STIMULI_PER_BLOCK'] * self.constants['TRIAL_DURATION']


        last_target_idx = -1
        last_target_event_onset = np.nan

        for j_miniblock, category in enumerate(self.miniblock_categories):
            #miniblock_clock.reset()

            if category == 'baseline':
                self.fixation.draw(exp_win)
                utils.wait_until(
                    self.task_timer,
                    self.constants['COUNTDOWN_DURATION'] + j_miniblock * block_duration)
                yield True
                # todo response + log

                onset = self._exp_win_last_flip_time - self._exp_win_first_flip_time

                self._events.append({
                    'trial_type': 'rest'
                    'onset': onset,
                    'block': j_miniblock,
                    'category': category,
                })
            else:
                # Block of stimuli
                miniblock_stimuli = list(np.random.choice(
                    self.stimuli[category], size=self.constants['N_STIMULI_PER_BLOCK'], replace=False))
                if self.task_miniblocks[nonbaseline_block_counter] == 1:
                    # Check for last block's target to make sure that two targets don't
                    # occur within the same response exp_win
                    if (j_miniblock > 0) and (target_idx is not None):
                        last_target_onset = (((self.constants['N_STIMULI_PER_BLOCK'] + 1) - target_idx) *
                                             self.constants['TRIAL_DURATION'] * -1)
                        last_target_rw_offset = last_target_onset + self.constants['RESPONSE_WINDOW']
                        first_viable_trial = int(np.ceil(last_target_rw_offset /
                                                         self.constants['TRIAL_DURATION']))
                        first_viable_trial = np.maximum(0, first_viable_trial)
                        first_viable_trial += 1  # just to give it a one-trial buffer
                    else:
                        first_viable_trial = 0

                    # Adjust stimuli based on task
                    if self.task == 'Oddball':
                        # target is scrambled image
                        target_idx = np.random.randint(first_viable_trial, len(miniblock_stimuli))
                        miniblock_stimuli[target_idx] = np.random.choice(self.stimuli['scrambled'])
                    elif self.task == 'OneBack':
                        # target is second stim of same kind
                        first_viable_trial = np.maximum(first_viable_trial, 1)
                        target_idx = np.random.randint(first_viable_trial, len(miniblock_stimuli))
                        miniblock_stimuli[target_idx] = miniblock_stimuli[target_idx - 1]
                    elif self.task == 'TwoBack':
                        # target is second stim of same kind
                        first_viable_trial = np.maximum(first_viable_trial, 2)
                        target_idx = np.random.randint(first_viable_trial, len(miniblock_stimuli))
                        miniblock_stimuli[target_idx] = miniblock_stimuli[target_idx - 2]
                    last_target_idx = target_idx
                else:
                    target_idx = None

                for k_stim, stim_file in enumerate(miniblock_stimuli):

                    self.stim_image.image = stim_file
                    self.stim_image.draw(exp_win)
                    self.fixation.draw(exp_win)
                    utils.wait_until(
                        self.task_timer,
                        self.constants['COUNTDOWN_DURATION'] + \
                        j_miniblock * block_duration + \
                        k_stim * self.constants["TRIAL_DURATION"])
                    yield True

                    is_target = target_idx == k_stim
                    onset = self._exp_win_last_flip_time - self._exp_win_first_flip_time

                    self.fixation.draw(exp_win)
                    utils.wait_until(
                        self.task_timer,
                        self.constants['COUNTDOWN_DURATION'] + \
                        j_miniblock * block_duration + \
                        k_stim * self.constants["TRIAL_DURATION"] + \
                        self.constants["IMAGE_DURATION"])
                    yield True

                    offset = self._exp_win_last_flip_time - self._exp_win_first_flip_time
                    self._events.append({
                        'trial_type': 'stimuli',
                        'onset': onset,
                        'offset': offset,
                        'block': j_miniblock,
                        'category': category,
                        'block_trial': k_stim,
                        'duration': offset-onset,
                        'target': is_target,
                    })
                    if is_target:
                        last_target_event_onset = onset


                    keypresses = event.getKeys(self.RESPONSE_KEYS, timeStamped=self.task_timer)
                    for k in keypresses:
                        rt = k[1] - last_target_event_onset
                        self._events.append({
                            'trial_type': 'keypress',
                            'onset': k[1],
#                            'match_target': (k_stim-last_target_idx < 1 if last_target_idx>=0 else None), #consider a correct response if in current of previous image
                            'reaction_time': rt,
                            'task': self.task,
                        })

                nonbaseline_block_counter += 1
        utils.wait_until(
            self.task_timer,
            self.constants['COUNTDOWN_DURATION'] + \
            len(self.miniblock_categories) * block_duration + \
            self.constants['END_SCREEN_DURATION']
            )

    def _stop(self, exp_win, ctl_win):
        exp_win.setColor((0,0,0), "rgb")
        for _ in range(2):
            yield True


def randomize_carefully(elems, n_repeat=2):
    """
    Shuffle without consecutive duplicates
    From https://stackoverflow.com/a/22963275/2589328
    """
    s = set(elems)
    res = []
    for n in range(n_repeat):
        if res:
            # Avoid the last placed element
            lst = list(s.difference({res[-1]}))
            # Shuffle
            np.random.shuffle(lst)
            lst.append(res[-1])
            # Shuffle once more to avoid obvious repeating patterns in the last position
            lst[1:] = np.random.choice(lst[1:], size=len(lst)-1, replace=False)
        else:
            lst = elems[:]
            np.random.shuffle(lst)
        res.extend(lst)
    return res
