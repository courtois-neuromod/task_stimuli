import os, sys, time, random
import numpy as np
from psychopy import visual, core, data, logging
from .task_base import Task
from .task_base import Fixation

from ..shared import config

STIMULI_DURATION = 1
BASELINE_BEGIN = 1
BASELINE_END = 1
ISI_mean = 2
ISI_base = 2
IMAGES_FOLDER = "/Users/xiaoxuanlei/Desktop/202209_MULTFS_mri/task_stimuli-main/data/multfs/MULTIF_4_stim"

STIMULI_SIZE = (400, 400)

triplet_id_to_pos = [(0,0), (-200, 0), (200, 0), ]


class multfs_dms(Task):

    DEFAULT_INSTRUCTION = """You will be presented a set of items in different quadrant of the screen.
Try to remember the items and their location on the screen."""

    def __init__(self, items_list, *args, **kwargs):
        super().__init__(**kwargs)
        self.item_list = data.importConditions(items_list)
        self.temp_dict = {}
        self.instruction = instructions_converter(self.name)


    def setup(
            self,
            exp_win,
            output_path = None,
            output_fname_base = None,
            use_fmri=False,
            use_meg=False,
    ):
        self.output_path = output_path
        self.output_fname_base = output_fname_base
        self.use_fmri = use_fmri
        self.use_meg = use_meg
        self._events = []

        self._exp_win_first_flip_time = None
        self._exp_win_last_flip_time = None
        self._ctl_win_last_flip_time = None
        self._task_completed = False
        self.fixation = visual.TextStim(exp_win, text="+", alignText="center", color="white")

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

    def instructions(self, exp_win, ctl_win = None, is_instruction = True, ):

        if hasattr(self, "_instructions"):
            for clearBuffer in self._instructions(exp_win,ctl_win):
                # yield
                self._flip_all_windows(exp_win, ctl_win, clearBuffer)

        # 2 flips to clear screen
        for i in range(2):
            # yield
            self._flip_all_windows(exp_win, ctl_win, True)

    def _flip_all_windows(self, exp_win, ctl_win=None, clearBuffer=True):

        exp_win.flip(clearBuffer=clearBuffer)
        # set callback for next flip, to be the first callback for other callbacks to use
        exp_win.timeOnFlip(self.temp_dict, 'exp_win_last_flip_time')

    def _run(self, exp_win, ctl_win):

        trials = data.TrialHandler(self.item_list, 1, method="random")
        img = visual.ImageStim(exp_win, size=STIMULI_SIZE, units="pix")
        exp_win.logOnFlip(
            level=logging.EXP, msg="memory: task starting at %f" % time.time()
        )
        for frameN in range(config.FRAME_RATE * BASELINE_BEGIN):
            yield ()
        for trial in trials:
            self._flip_all_windows(exp_win, ctl_win, clearBuffer=True)
            ISI = int(np.floor(np.random.normal(ISI_mean))) # todo: ISI has to be an integer!
            for i in range(1,3):
                if i == 1: img_index = "a"
                else: img_index = "b"
                image_path = trial["stim_%s" % img_index]
                img.image = IMAGES_FOLDER + "/" + str(image_path) + "/image.png"
                img.pos = triplet_id_to_pos[trial["loc_%s" % img_index]]
                exp_win.logOnFlip(
                    level=logging.EXP,
                    msg="memory: display %s in quadrant %s"
                    % (str(img.image), str(img.pos)),
                )
                for frameN in range(config.FRAME_RATE * STIMULI_DURATION):

                    img.draw(exp_win)
                    if i == 1:
                        self.fixation.draw(exp_win)
                    if ctl_win:
                        img.draw(ctl_win)
                    yield True
                exp_win.logOnFlip(level=logging.EXP, msg="memory: rest")
                if i == 1:
                    for frameN in range(config.FRAME_RATE * ISI):
                        self.fixation.draw(exp_win)
                        yield True
            else:
                for frameN in range(config.FRAME_RATE * ISI_base):
                    yield True


        for frameN in range(config.FRAME_RATE * BASELINE_END):
            yield ()

    def run(self, exp_win, ctl_win = None):
        self.instructions(exp_win, ctl_win= ctl_win)

        exp_win.timeOnFlip(self.temp_dict, 'exp_win_first_flip_time') # the original code does not work?
        self._flip_all_windows(exp_win, ctl_win, True)
        self._exp_win_first_flip_time = self.temp_dict["exp_win_first_flip_time"]
        #sync to first screen flip
        self.task_timer = core.MonotonicClock(self._exp_win_first_flip_time)

        # if self.progress_bar:
        #     self.progress_bar.reset() # todo: progress_bar not working?
        flip_idx = 0

        for clearBuffer in self._run(exp_win, ctl_win):
            # yield first to allow external draw before flip # this is not working?
            # yield
            self._flip_all_windows(exp_win, ctl_win, clearBuffer)
            # increment the progress bar depending on task flip rate
            # if self.progress_bar:
            #     if self._progress_bar_refresh_rate and flip_idx % self._progress_bar_refresh_rate == 0:
            #         self.progress_bar.update(1)
            flip_idx += 1
        self._task_completed = True

def instructions_converter(task_name):
    ins_dict = {
        "multfs_dms_loc": "press LEFT if two stimulus are at the same location, otherwise press RIGHT",
        "multfs_dms_cat": "press LEFT if two stimulus belong to the same category, otherwise press RIGHT",
        "multfs_dms_obj": "press LEFT if two stimulus are the same object, otherwise press RIGHT",
        "multfs_dms_ang": "press lEFT if two stimulus have the same angle, otherwise press RIGHT",
        "multfs_1back_loc": """
                    In this task, you will see a sequence of stimulus presented one after another. 
                    Press LEFT each time the current stimulus is at the same location as the one presented just before.
                    Otherwise press RIGHT
                    """,
        "multfs_1back_obj": """
                    In this task, you will see a sequence of stimulus presented one after another. 
                    Press LEFT each time the current stimulus is the same object as the one presented just before.
                    Otherwise press RIGHT
                    """,
        "multfs_1back_cat": """
                    In this task, you will see a sequence of stimulus presented one after another. 
                    Press LEFT each time the current stimulus belong to the same category as the one presented just before.
                    Otherwise press RIGHT
                    """,
        "multfs_1back_ang": """
                    In this task, you will see a sequence of stimulus presented one after another. 
                    Press LEFT each time the current stimulus has the same angle as the one presented just before.
                    Otherwise press RIGHT
                    """,

        "multfs_2back_loc": """
                        In this task, you will see a sequence of stimulus presented one after another. 
                        Press LEFT each time the current stimulus is at the same location as the one presented before last.
                        Otherwise press RIGHT
                        """,
        "multfs_2back_obj": """
                        In this task, you will see a sequence of stimulus presented one after another. 
                        Press LEFT each time the current stimulus is the same object as the one presented before last.
                        Otherwise press RIGHT
                        """,
        "multfs_2back_cat": """
                        In this task, you will see a sequence of stimulus presented one after another. 
                        Press LEFT each time the current stimulus belong to the same category as the one presented before last.
                        Otherwise press RIGHT
                        """,
        "multfs_2back_ang": """
                        In this task, you will see a sequence of stimulus presented one after another. 
                        Press LEFT each time the current stimulus has the same angle as the one presented before last.
                        Otherwise press RIGHT
                        """,
        "multfs_seqDMS_loc": """
                        In this task, you will see a sequence of stimulus (2) presented one after another followed by another sequence of stimulus (2).
                        Press LEFT at the end of the trial if the second sequence of stimulus matches the first sequence of stimulus in terms of location.
                        Otherwise press LEFT 
                        """,
        "multfs_seqDMS_cat": """
                        In this task, you will see a sequence of stimulus (2) presented one after another followed by another sequence of stimulus (2).
                        Press LEFT at the end of the trial if the second sequence of stimulus matches the first sequence of stimulus in terms of Category.
                        Otherwise press LEFT 
                        """,
        "multfs_seqDMS_obj": """
                        In this task, you will see a sequence of stimulus (2) presented one after another followed by another sequence of stimulus (2).
                        Press LEFT at the end of the trial if the second sequence of stimulus matches the first sequence of stimulus in terms of Object.
                        Otherwise press LEFT 
                        """,
        "multfs_seqDMS_ang": """
                        In this task, you will see a sequence of stimulus (2) presented one after another followed by another sequence of stimulus (2).
                        Press LEFT at the end of the trial if the second sequence of stimulus matches the first sequence of stimulus in terms of View Angle.
                        Otherwise press LEFT 
                        """,

    }
    return ins_dict[task_name]
