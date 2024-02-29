import os, sys, time
from psychopy import visual, core, data, logging, sound, event
from pandas import read_csv
from .task_base import Task
from colorama import Fore

from ..shared import config, utils
from ..shared.eyetracking import fixation_dot

TR = 1.49
STIMULI_DURATION = 4

TRIPLET_RIGHT_KEY = "l"
TRIPLET_LEFT_KEY = "d"
MOVE_ON = "d"


BASELINE_BEGIN = 6
BASELINE_END = 9
ISI = 4*TR - STIMULI_DURATION
INSTRUCTION_DURATION = 10
RESPONSE_DURATION=ISI


class Triplet(Task):

    DEFAULT_INSTRUCTION = """You will see three words - we ask you to select the one that is NOT related in meaning.


Don't think too much and give the first answer that comes to mind.
"""

    RESPONSE_KEYS = ['x','a','b']
    RESPONSE_TEXT = {
        'x':'1',
        'a':'2',
        'b':'3',
    }

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

        screen_text.draw(exp_win)
        if ctl_win:
            screen_text.draw(ctl_win)
        yield True
        time.sleep(INSTRUCTION_DURATION)
        yield True

    def _setup(self, exp_win):
        self.r0_stim = visual.TextStim(
            exp_win, text="", pos=(0, 0.5), alignText="center", color="white"
        )

        self.r1_stim = visual.TextStim(
            exp_win, text="", pos=(0, 0), alignText="center", color="white"
        )

        self.r2_stim = visual.TextStim(
            exp_win, text="", pos=(0, -0.5), alignText="center", color="white"
        )

        self.trials = data.TrialHandler(self.words_list, 1, method="sequential")

        self.duration = len(self.words_list)
        self._progress_bar_refresh_rate = 2
        self.fixation = fixation_dot(exp_win)

    def _run(self, exp_win, ctl_win):
        for stim in self.fixation:
            stim.draw(exp_win)
        yield True

        for trial_n, trial in enumerate(self.trials):

            # randomization
            all_stim = [trial["target"],trial["choice_1"],trial["choice_2"]]
            from random import shuffle
            shuffle(all_stim)
            self.r0_stim.text = all_stim[0]
            self.r1_stim.text = all_stim[1]
            self.r2_stim.text = all_stim[2]

            exp_win.winHandle.activate()

            for stim in [self.r0_stim, self.r1_stim, self.r2_stim]:
                stim.draw(exp_win)
                if ctl_win:
                    stim.draw(ctl_win)

            exp_win.logOnFlip(level=logging.EXP, msg="triplet: %d" % trial_n)

            # wait onset
            utils.wait_until(self.task_timer, trial["onset"] - 1 / config.FRAME_RATE)
            keypresses = event.getKeys(self.RESPONSE_KEYS) # flush response keys
            yield True # flip
            trial["onset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )
            self.progress_bar.set_description(
                f"Trial {trial_n}:: {trial['target']}"
            )

            for stim in self.fixation:
                stim.draw(exp_win)
            utils.wait_until(self.task_timer, trial["onset"] + trial["duration"] - 1 / config.FRAME_RATE)
            yield True
            trial["offset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )
            # wait until .1s before the next trial, leaving time to prepare it
            utils.wait_until(self.task_timer, trial["onset"] + trial["duration"] + trial['isi'] - .1)

            self.trials.addData("w1", all_stim[0])
            self.trials.addData("w2", all_stim[1])
            self.trials.addData("w3", all_stim[2])
            # record keypresses
            triplet_answer_keys = event.getKeys(self.RESPONSE_KEYS, timeStamped=self.task_timer)
            if len(triplet_answer_keys):
                first_response = triplet_answer_keys[0]
                self.trials.addData("answer", first_response[0])
                self.trials.addData("answer_onset", first_response[1])
                self.trials.addData("response_txt",self.RESPONSE_TEXT[first_response[0]])
                self.trials.addData("response_time", first_response[1]-trial["onset_flip"])
                self.progress_bar.set_description(
                    f"Trial {trial_n}:: {trial['target']}: \u2705")
            else:
                for k in ['answer', 'answer_onset', 'response_txt','response_time']:
                    trial[k] = ''
                self.progress_bar.set_description(
                    f"{Fore.RED}Trial {trial_n}:: {trial['target']}: no response{Fore.RESET}")
            self.trials.addData("all_keys", triplet_answer_keys)

        # wait for end of run baseline
        utils.wait_until(self.task_timer, trial["onset"] + trial["duration"] + trial['isi'] + BASELINE_END)

    def _save(self):
        self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
        return False

class WordFeatures(Task):

    DEFAULT_INSTRUCTION = """You will be presented single words and asked questions about it."""

    SENSORIMOTOR_QUESTION = """Press A if you experience the word {sensorimotor_feature}.
Press B if you don’t know the word."""

    RESPONSE_KEYS = ['a', 'b']
    RESPONSE_TEXT = {
        'a':'yes',
        'b':'unknown',
    }

    def __init__(self, words_file, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

        screen_text.draw(exp_win)
        if ctl_win:
            screen_text.draw(ctl_win)
        yield True
        time.sleep(INSTRUCTION_DURATION)
        yield True

    def _setup(self,exp_win):
        self.text = visual.TextStim(
            exp_win, text="", pos=(0, 0), alignText="center", color="white"
        )
        self.duration = len(self.words_list)
        self._progress_bar_refresh_rate = 2
        self.trials = data.TrialHandler(self.words_list, 1, method="sequential")


    def _run(self, exp_win, ctl_win):
        yield True
        for trial_n, trial in enumerate(self.trials):

            if trial['trial_type'] == 'feature_question':
                self.text.bold = True
                self.text.text = self.SENSORIMOTOR_QUESTION.format(**trial)
                self.progress_bar.set_description(
                    f"Block {trial['block_index']}:: {trial['sensorimotor_feature']}"
                )
            else:
                self.text.bold = False
                self.text.text = trial['word']
                self.progress_bar.set_description(
                    f"Trial :: {trial['word']}"
                )

            self.text.draw(exp_win)
            if ctl_win:
                self.text.draw(ctl_win)

            #force focus
            exp_win.winHandle.activate()
            utils.wait_until(self.task_timer, trial["onset"] - 1 / config.FRAME_RATE)
            keypresses = event.getKeys(self.RESPONSE_KEYS) # flush response keys
            yield True # flip
            trial["onset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )

            utils.wait_until(self.task_timer, trial["onset"] + trial["duration"] - 1 / config.FRAME_RATE)
            yield True
            trial["offset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )
            # wait until .1s before the next trial, leaving time to prepare it
            utils.wait_until(self.task_timer, trial["onset"] + trial["duration"] + trial['isi'] - .1)

            # record keypresses
            answer_keys = event.getKeys(self.RESPONSE_KEYS, timeStamped=self.task_timer)
            if len(answer_keys):
                first_response = answer_keys[0]
                self.trials.addData("answer", first_response[0])
                self.trials.addData("answer_onset", first_response[1])
                self.trials.addData("answer_text", self.RESPONSE_TEXT[first_response[0]])
                self.trials.addData("response_time", first_response[1]-trial["onset_flip"])
                self.progress_bar.set_description(
                    f"Trial {trial_n}:: {trial['word']}: \u2705")
            else:
                for k in ['answer', 'answer_onset', 'answer_text', 'response_time']:
                    trial[k] = ''
            self.trials.addData("all_keys", answer_keys)
            utils.wait_until(self.task_timer, trial["onset"] + trial["duration"] + trial['isi'] - .1)

        # wait for end of run baseline
        utils.wait_until(self.task_timer, trial["onset"] + trial["duration"] + trial['isi'] + BASELINE_END)

    def _save(self):
        self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
        return False

class WordFamiliarity(Task):

    DEFAULT_INSTRUCTION = """You will be presented single words.
    Please rate how familiar are you with that concept from 1 (unfamiliar) to 3 (familiar)"""

    RESPONSE_KEYS = ['b','a','x']
    RESPONSE_TEXT = {
        'b':'1',
        'a':'2',
        'x':'3',
    }

    def __init__(self, words_file, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

        screen_text.draw(exp_win)
        if ctl_win:
            screen_text.draw(ctl_win)
        yield True
        time.sleep(INSTRUCTION_DURATION)
        yield True

    def _setup(self,exp_win):
        self.text = visual.TextStim(
            exp_win, text="", pos=(0, 0), alignText="center", color="white"
        )
        self.duration = len(self.words_list)
        self._progress_bar_refresh_rate = 2
        self.trials = data.TrialHandler(self.words_list, 1, method="sequential")
        self.fixation = fixation_dot(exp_win)


    def _run(self, exp_win, ctl_win):
        for stim in self.fixation:
            stim.draw(exp_win)
        yield True
        for trial_n, trial in enumerate(self.trials):
            if trial['trial_type'] != 'word':
                continue

            self.text.bold = False
            self.text.text = trial['word']
            self.progress_bar.set_description(
                f"Trial :: {trial['word']}"
            )

            self.text.draw(exp_win)
            if ctl_win:
                self.text.draw(ctl_win)

            #force focus
            exp_win.winHandle.activate()
            utils.wait_until(self.task_timer, trial["onset"] - 1 / config.FRAME_RATE)
            keypresses = event.getKeys(self.RESPONSE_KEYS) # flush response keys
            yield True # flip
            trial["onset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )

            for stim in self.fixation:
                stim.draw(exp_win)
            utils.wait_until(self.task_timer, trial["onset"] + trial["duration"] - 1 / config.FRAME_RATE)
            yield True
            trial["offset_flip"] = (
                self._exp_win_last_flip_time - self._exp_win_first_flip_time
            )
            trial["duration_flip"] = trial["offset_flip"] - trial["onset_flip"]
            # wait until .1s before the next trial, leaving time to prepare it
            utils.wait_until(self.task_timer, trial["onset"] + trial["duration"] + trial['isi'] - .1)

            # record keypresses
            answer_keys = event.getKeys(self.RESPONSE_KEYS, timeStamped=self.task_timer)
            if len(answer_keys):
                first_response = answer_keys[0]
                self.trials.addData("answer", first_response[0])
                self.trials.addData("answer_onset", first_response[1])
                self.trials.addData("answer_text", self.RESPONSE_TEXT[first_response[0]])
                self.trials.addData("response_time", first_response[1]-trial["onset_flip"])
                self.progress_bar.set_description(
                    f"Trial {trial_n}:: {trial['word']}: \u2705")
            else:
                for k in ['answer', 'answer_onset', 'answer_text', 'response_time']:
                    trial[k] = ''

        # wait for end of run baseline
        utils.wait_until(self.task_timer, trial["onset"] + trial["duration"] + trial['isi'] + BASELINE_END)

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
            units='pix',
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

class Listening(Task):

    DEFAULT_INSTRUCTION = """You are about to listen to audio stimuli"""

    INSTRUCTION_WAIT_KEY = (
        DEFAULT_INSTRUCTION + "\nWhen you're ready press <%s>" % MOVE_ON
    )

    def __init__(self, filepath, *args, **kwargs):
        self.wait_key = kwargs.pop("wait_key", False)
        super().__init__(**kwargs)
        if self.wait_key:
            self.instruction = Listening.INSTRUCTION_WAIT_KEY
        self.filepath = filepath
        if not os.path.exists(self.filepath):
            raise ValueError("File %s does not exists" % self.filepath)

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
                if len(event.getKeys([MOVE_ON])):
                    break
                _draw_instr()
                yield
        else:
            for frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
                _draw_instr()
                yield

    def _run(self, exp_win, ctl_win):
        recording = sound.Sound(self.filepath)
        nextFlip = exp_win.getFutureFlipTime(clock='ptb')
        recording.play(when=nextFlip)  # sync with screen refresh
        exp_win.flip()
        event.waitKeys()

    def _save(self):
        self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
        return False

class ListeningBlocks(Task):
    """docstring for ListeningBlocks."""

    def __init__(self, design_file, stimuli_path, *args, instruction=None, **kwargs):
        super(ListeningBlocks, self).__init__(*args, **kwargs)
        self.design_file = design_file
        self.stimuli_path = stimuli_path
        self.instruction = instruction
        self.design = data.importConditions(design_file)

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

    def _setup(self, exp_win):
        self.trials = data.TrialHandler(self.design, 1, method="sequential")
        self.fixation_dot = fixation_dot(exp_win)
        self._stimuli = [
            (sound.Sound(
                os.path.join(self.stimuli_path, trial['stim_file'])) \
                if trial['stim_file'] else None) \
            for trial in self.design]
        super()._setup(exp_win)
        self.current_stimuli = None

    def _run(self, exp_win, ctl_win):

        for trial_n, (trial, self.current_stimuli) in enumerate(zip(self.trials, self._stimuli)):
            if trial['trial_type'] == 'fix':
                for stim_ in self.fixation_dot:
                    stim_.draw(exp_win)
                if trial_n > 0:
                    utils.wait_until(self.task_timer, trial['onset'] - 1/config.FRAME_RATE)

            if self.current_stimuli:
                self.current_stimuli.play(when = self.task_timer._timeAtLastReset + trial['onset'])
            yield True
            for _ in utils.wait_until_yield(
                self.task_timer,
                trial['onset']+trial['duration'] - 2/config.FRAME_RATE,
                keyboard_accuracy=.1):
                yield True
            if self.current_stimuli:
                if self.current_stimuli.status > 0:
                        logging.warning('trial ended before the sound finished playing: check files durations')
                self.current_stimuli.stop()

    def _stop(self, exp_win, ctl_win):
        if self.current_stimuli:
            self.current_stimuli.stop()
        yield

    def _restart(self):
        self.trials = data.TrialHandler(self.design, 1, method="sequential")

    def _save(self):
        self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
        return False

    def unload(self):
        del self._stimuli

class ReadingBlocks(Task):
    """docstring for ReadingBlocks."""

    def __init__(self, design_file, *args, instruction=None,
        txt_color="black", txt_font="Palatino Linotype", txt_size=42,
        bg_color=(.5, .5, .5), press_key='a', **kwargs):
        super(ReadingBlocks, self).__init__(*args, **kwargs)
        self.design_file = design_file
        self.design = data.importConditions(design_file)
        self.txt_color = txt_color
        self.txt_font = txt_font
        self.txt_size = txt_size
        self.bg_color = bg_color
        self.instruction = instruction
        self.press_key = press_key

    def _setup(self, exp_win):
        self.trials = data.TrialHandler(self.design, 1, method="sequential")
        self.fixation_dot = fixation_dot(exp_win)
        self.txt_stim = visual.TextStim(
            exp_win,
            text="+",
            font=self.txt_font,
            height=self.txt_size,
            units='pix',
            alignText="center",
            color=self.txt_color,
        )

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
        last_press_trial = None
        for trial_n, trial in enumerate(self.trials):
            if trial['trial_type'] == 'fix':
                for stim_ in self.fixation_dot:
                    stim_.draw(exp_win)
            else:
                if trial['trial_type'] == 'press':
                    last_press_trial = trial
                    self.txt_stim.text = ':'
                else:
                    self.txt_stim.text = trial['word']
                self.txt_stim.draw(exp_win)
            if trial_n > 0: #
                utils.wait_until(self.task_timer, trial['onset'] - 1/config.FRAME_RATE)
            else: # force assignt to none, otherwise future trial will just dismiss the added fields
                for k in ['all_keypresses', 'response_onset', 'response_time']:
                    trial[k] = None
            yield True
            trial['onset_flip'] = self._exp_win_last_flip_time - self._exp_win_first_flip_time
            yield from utils.wait_until_yield(
                self.task_timer,
                trial['onset']+trial['duration'] - 2/config.FRAME_RATE,
                keyboard_accuracy=.1)
            trial['offset_flip'] = self._exp_win_last_flip_time - self._exp_win_first_flip_time
            kpress = event.getKeys([self.press_key], timeStamped=self.task_timer)
            if len(kpress) and last_press_trial:
                last_press_trial['all_keypresses'] = last_press_trial.get('all_keypresses', []) + kpress
                if not last_press_trial.get('response_onset', None):
                    last_press_trial['response_onset'] = kpress[0][1]
                    last_press_trial['response_time'] = kpress[0][1] - last_press_trial['onset_flip']

    def _restart(self):
        self.trials = data.TrialHandler(self.design, 1, method="sequential")

    def _save(self):
        self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
        return False
