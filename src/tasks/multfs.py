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
IMAGES_FOLDER = "data/multfs/MULTIF_4_stim"
STIMULI_SIZE = (400, 400)

triplet_id_to_pos = [(0,0), (-200, 0), (200, 0), ]


class multfs_base(Task):

    def __init__(self, items_list, *args, **kwargs):
        super().__init__(**kwargs)
        self.item_list = data.importConditions(items_list)
        self.temp_dict = {}
        self.instruction = instructions_converter(self.name)


    def _setup(self, exp_win):
        self.fixation = visual.TextStim(exp_win, text="+", alignText="center", color="white")
        super()._setup(exp_win)

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

class multfs_dms(multfs_base):

    def _run(self, exp_win, ctl_win):

        trials = data.TrialHandler(self.item_list, 1, method="random")
        img = visual.ImageStim(exp_win, size=STIMULI_SIZE, units="pix")
        exp_win.logOnFlip(
            level=logging.EXP, msg="memory: task starting at %f" % time.time()
        )
        for frameN in range(config.FRAME_RATE * BASELINE_BEGIN):
            yield ()
        for trial in trials:
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

class multfs_1back(multfs_base):

    def __init__(self, items_list, *args, seq_len=6, **kwargs):
        super().__init__(items_list, **kwargs)
        self.seq_len = seq_len

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
            for i in range(1,self.seq_len + 1):
                if i == 1: img_index = "a"
                elif i == 2: img_index = "b"
                elif i == 3: img_index = "c"
                elif i == 4: img_index = "d"
                elif i == 5: img_index = "e"
                elif i == 6: img_index = "f"

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
                if i != self.seq_len:
                    for frameN in range(config.FRAME_RATE * ISI):
                        self.fixation.draw(exp_win)
                        yield True
                else:
                    for frameN in range(config.FRAME_RATE * ISI):
                        yield True
                # exp_win.logOnFlip(level=logging.EXP, msg="memory: next stimulus")
            else:
                for frameN in range(config.FRAME_RATE * ISI_base):
                    yield True


        for frameN in range(config.FRAME_RATE * BASELINE_END):
            yield ()


class multfs_ctx(multfs_base):

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

class multfs_interdms_AABB(multfs_base):

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
            for i in range(1,5):
                image_path = trial["frame_obj_%d" % i]
                img.image = IMAGES_FOLDER + "/" + str(image_path) + "/image.png"
                img.pos = triplet_id_to_pos[trial["frame_loc_%s" % i]]
                exp_win.logOnFlip(
                    level=logging.EXP,
                    msg="memory: display %s in quadrant %s"
                    % (str(img.image), str(img.pos)),
                )
                for frameN in range(config.FRAME_RATE * STIMULI_DURATION):

                    img.draw(exp_win)
                    if i == 2 or i == 4:
                        self.fixation.draw(exp_win)
                    if ctl_win:
                        img.draw(ctl_win)
                    yield True
                exp_win.logOnFlip(level=logging.EXP, msg="memory: rest")
                if i == 2 or i == 4:
                    for frameN in range(config.FRAME_RATE * ISI):
                        self.fixation.draw(exp_win)
                        yield True
            else:
                for frameN in range(config.FRAME_RATE * ISI_base):
                    yield True


        for frameN in range(config.FRAME_RATE * BASELINE_END):
            yield ()

class multfs_interdms_ABBA(multfs_base):

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
            for i in range(1,5):
                image_path = trial["frame_obj_%d" % i]
                img.image = IMAGES_FOLDER + "/" + str(image_path) + "/image.png"
                img.pos = triplet_id_to_pos[trial["frame_loc_%s" % i]]
                exp_win.logOnFlip(
                    level=logging.EXP,
                    msg="memory: display %s in quadrant %s"
                    % (str(img.image), str(img.pos)),
                )
                for frameN in range(config.FRAME_RATE * STIMULI_DURATION):

                    img.draw(exp_win)
                    if i == 3 or i == 4:
                        self.fixation.draw(exp_win)
                    if ctl_win:
                        img.draw(ctl_win)
                    yield True
                exp_win.logOnFlip(level=logging.EXP, msg="memory: rest")
                if i == 3 or i == 4:
                    for frameN in range(config.FRAME_RATE * ISI):
                        self.fixation.draw(exp_win)
                        yield True
            else:
                for frameN in range(config.FRAME_RATE * ISI_base):
                    yield True


        for frameN in range(config.FRAME_RATE * BASELINE_END):
            yield ()

class multfs_interdms_ABAB(multfs_base):

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
            for i in range(1,5):
                image_path = trial["frame_obj_%d" % i]
                img.image = IMAGES_FOLDER + "/" + str(image_path) + "/image.png"
                img.pos = triplet_id_to_pos[trial["frame_loc_%s" % i]]
                exp_win.logOnFlip(
                    level=logging.EXP,
                    msg="memory: display %s in quadrant %s"
                    % (str(img.image), str(img.pos)),
                )
                for frameN in range(config.FRAME_RATE * STIMULI_DURATION):

                    img.draw(exp_win)
                    if i == 3 or i == 4:
                        self.fixation.draw(exp_win)
                    if ctl_win:
                        img.draw(ctl_win)
                    yield True
                exp_win.logOnFlip(level=logging.EXP, msg="memory: rest")
                if i == 3 or i == 4:
                    for frameN in range(config.FRAME_RATE * ISI):
                        self.fixation.draw(exp_win)
                        yield True
            else:
                for frameN in range(config.FRAME_RATE * ISI_base):
                    yield True


        for frameN in range(config.FRAME_RATE * BASELINE_END):
            yield ()

def instructions_converter(task_name):
    task = task_name[5:].split('_run')[0]
    task = f"multfs_{task}"

    ins_dict = {
        "multfs_dmsloc": "press LEFT if two stimulus are at the same location, otherwise press RIGHT",
        "multfs_dmscat": "press LEFT if two stimulus belong to the same category, otherwise press RIGHT",
        "multfs_dmsobj": "press LEFT if two stimulus are the same object, otherwise press RIGHT",
        "multfs_dmsang": "press lEFT if two stimulus have the same angle, otherwise press RIGHT",
        "multfs_interdmsloc_AABB": """
                          Press LEFT on the second frame if the first and second stimuli have the same location,  otherwise press RIGHT.
                          Press LEFT on the fourth frame if the third and fourth stimuli have the same location,  otherwise press RIGHT. 
                          """,
        "multfs_interdmscat_AABB": """
                              Press LEFT on the second frame if the first and second stimuli have the same category,  otherwise press RIGHT.
                              Press LEFT on the fourth frame if the third and fourth stimuli have the same category,  otherwise press RIGHT. 
                              """,
        "multfs_interdmsobj_AABB": """
                              Press LEFT on the second frame if the first and second stimuli are the same object,  otherwise press RIGHT.
                              Press LEFT on the fourth frame if the third and fourth stimuli are the same object,  otherwise press RIGHT. 
                              """,
        "multfs_interdmsloc_ABBA": """
                              Press LEFT on the fourth frame if the first and fourth stimuli have the same location,  otherwise press RIGHT.
                              Press LEFT on the third frame if the second and third stimuli have the same location,  otherwise press RIGHT. 
                              """,
        "multfs_interdmscat_ABBA": """
                                  Press LEFT on the fourth frame if the first and fourth stimuli have the same category,  otherwise press RIGHT.
                                  Press LEFT on the third frame if the second and third stimuli have the same category,  otherwise press RIGHT. 
                                  """,
        "multfs_interdmsobj_ABBA": """
                                  Press LEFT on the fourth frame if the first and fourth stimuli are the same object,  otherwise press RIGHT.
                                  Press LEFT on the third frame if the third and third stimuli are the same object,  otherwise press RIGHT. 
                                  """,
        "multfs_interdmsloc_ABAB": """
                              Press LEFT on the third frame if the first and third stimuli have the same location,  otherwise press RIGHT.
                              Press LEFT on the fourth frame if the second and fourth stimuli have the same location,  otherwise press RIGHT. 
                              """,
        "multfs_interdmscat_ABAB": """
                                  Press LEFT on the third frame if the first and third stimuli have the same category,  otherwise press RIGHT.
                                  Press LEFT on the fourth frame if the second and fourth stimuli have the same category,  otherwise press RIGHT. 
                                  """,
        "multfs_interdmsobj_ABAB": """
                                  Press LEFT on the third frame if the first and third stimuli are the same object,  otherwise press RIGHT.
                                  Press LEFT on the fourth frame if the second and fourth stimuli are the same object,  otherwise press RIGHT. 
                                  """,
        "multfs_1backloc": """
                    In this task, you will see a sequence of stimulus presented one after another. Press LEFT each time the current stimulus is at the same location as the one presented just before. Otherwise press RIGHT
                    """,
        "multfs_1backobj": """
                    In this task, you will see a sequence of stimulus presented one after another. Press LEFT each time the current stimulus is the same object as the one presented just before. Otherwise press RIGHT
                    """,
        "multfs_1backcat": """
                    In this task, you will see a sequence of stimulus presented one after another. Press LEFT each time the current stimulus belong to the same category as the one presented just before. Otherwise press RIGHT
                    """,
        "multfs_1backang": """
                    In this task, you will see a sequence of stimulus presented one after another.
                    Press LEFT each time the current stimulus has the same angle as the one presented just before.
                    Otherwise press RIGHT
                    """,

        "multfs_2backloc": """
                        In this task, you will see a sequence of stimulus presented one after another.
                        Press LEFT each time the current stimulus is at the same location as the one presented before last.
                        Otherwise press RIGHT
                        """,
        "multfs_2backobj": """
                        In this task, you will see a sequence of stimulus presented one after another.
                        Press LEFT each time the current stimulus is the same object as the one presented before last.
                        Otherwise press RIGHT
                        """,
        "multfs_2backcat": """
                        In this task, you will see a sequence of stimulus presented one after another.
                        Press LEFT each time the current stimulus belong to the same category as the one presented before last.
                        Otherwise press RIGHT
                        """,
        "multfs_2backang": """
                        In this task, you will see a sequence of stimulus presented one after another.
                        Press LEFT each time the current stimulus has the same angle as the one presented before last.
                        Otherwise press RIGHT
                        """,
        "multfs_seqDMSloc": """
                        In this task, you will see a sequence of stimulus (2) presented one after another followed by another sequence of stimulus (2).
                        Press LEFT at the end of the trial if the second sequence of stimulus matches the first sequence of stimulus in terms of location.
                        Otherwise press LEFT
                        """,
        "multfs_seqDMScat": """
                        In this task, you will see a sequence of stimulus (2) presented one after another followed by another sequence of stimulus (2).
                        Press LEFT at the end of the trial if the second sequence of stimulus matches the first sequence of stimulus in terms of Category.
                        Otherwise press LEFT
                        """,
        "multfs_seqDMSobj": """
                        In this task, you will see a sequence of stimulus (2) presented one after another followed by another sequence of stimulus (2).
                        Press LEFT at the end of the trial if the second sequence of stimulus matches the first sequence of stimulus in terms of Object.
                        Otherwise press LEFT
                        """,
        "multfs_seqDMSang": """
                        In this task, you will see a sequence of stimulus (2) presented one after another followed by another sequence of stimulus (2).
                        Press LEFT at the end of the trial if the second sequence of stimulus matches the first sequence of stimulus in terms of View Angle.
                        Otherwise press LEFT
                        """,
        "multfs_ctxclo": """
                        If the presented two stimuli belong to the same category, press LEFT if they are at the same location, press RIGHT if not.
                        If the presented two stimuli does not belong to the same category, press LEFT if they are the same object, press RIGTH if not.
                        """,
        "multfs_ctxcol": """
                        If the presented two stimuli belong to the same category, press LEFT if they are the same object, press RIGTH if not.
                        If the presented two stimuli does not belong to the same category, press LEFT if they are at the same location, press RIGHT if not.
                        """,
        "multfs_ctxocl": """
                        If the presented two stimuli are the same object, press LEFT if they belong to the same category, press RIGTH if not.
                        If the presented two stimuli are not the same object, press LEFT if they are at the same location, press RIGHT if not.
                        """,
        "multfs_ctxolc": """
                        If the presented two stimuli are the same object, press LEFT if they are at the same location, press RIGHT if not.
                        If the presented two stimuli are not the same object, press LEFT if they belong to the same category, press RIGTH if not.
                        """,
        "multfs_ctxloc": """
                            If the presented two stimuli are at the same location, press LEFT if they are same object, press RIGHT if not.
                            If the presented two stimuli are not at the same location, press LEFT if they belong to the same category, press RIGTH if not.
                        """,
        "multfs_ctxlco": """
                        If the presented two stimuli are at the same location, press LEFT if they belong to the same category, press RIGTH if not.
                        If the presented two stimuli are not at the same location, press LEFT if they are same object, press RIGHT if not..
                    """,
    }
    return ins_dict[task]
