import os, sys, time, random
from psychopy import visual, core, data, logging, event, sound
import pandas
from .task_base import Task
from colorama import Fore

from ..shared import config, utils
from ..shared.eyetracking import fixation_dot

INSTRUCTION_DURATION = 4

class SoundTaskBase(Task):

    def __init__(self, sound_file, initial_wait=4, final_wait=9, *args, **kwargs):
        super().__init__(**kwargs)
        self.initial_wait, self.final_wait = initial_wait, final_wait
        if os.path.exists(sound_file):
            self.sound_file = sound_file
        else:
            raise ValueError("File %s does not exists" % sound_file)

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
        self.sound = sound.Sound(self.sound_file)
        self.fixation = fixation_dot(exp_win)
        self.duration = self.sound.duration

    def _run(self, exp_win, ctl_win):

        for _ in utils.wait_until_yield(
            self.task_timer,
            self.initial_wait,
            keyboard_accuracy=.1):
            for stim in self.fixation:
                stim.draw(exp_win)
            yield

        self.sound.play()
        for _ in utils.wait_until_yield(
            self.task_timer,
            self.initial_wait + self.sound.duration + self.final_wait,
            keyboard_accuracy=.1):
            yield
            self.progress_bar.n = int(self.task_timer.getTime())
            self.progress_bar.refresh()
        while self.sound.status > 0:
            pass
        print(f"{'#'*25} STOP SCANNER {'#'*25}")

    def _stop(self, exp_win, ctl_win):
        self.sound.stop()
        yield


class Story(SoundTaskBase):
    """docstring for Story."""

    DEFAULT_INSTRUCTION = """
Please listen to the following story carefully.
You will be asked a few questions once it is over..
"""


import pyaudio
import wave

class AudioRecording(Task):
    """docstring for AudioRecording."""

    INSTRUCTION_DURATION = 4

    def __init__(
        self,
        initial_wait=4, final_wait=9,
        max_duration=600, done_key='a',
        audio_rate=48000, audio_channels=1,
        *args, **kwargs):
        super().__init__(**kwargs)
        self.initial_wait, self.final_wait, self.max_duration = initial_wait, final_wait, max_duration
        self.audio_rate, self. audio_channels= audio_rate, audio_channels
        self.done_key = done_key
        self.duration = self.max_duration
        self._progress_bar_refresh_rate = None


    def _setup(self, exp_win,):

        """
        import psychopy.sound
        self._mic = psychopy.sound.Microphone(
            device = self.mic_device,
            channels = 1,
            maxRecordingSize = 24000 * (self.max_duration/60) # 24000~=62s
        )"""

        self._pyaudio_if = pyaudio.PyAudio()

        self.screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )
        self.fixation = fixation_dot(exp_win)


    def _instructions(self, exp_win, ctl_win):
        screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )

        for flip_idx, _ in enumerate(utils.wait_until_yield(
            core.monotonicClock,
            core.getTime()+ self.INSTRUCTION_DURATION,
            keyboard_accuracy=.01)):
            if flip_idx < 2:
                screen_text.draw(exp_win)
                if ctl_win:
                    screen_text.draw(ctl_win)
                yield True
            yield

    def _start_recording(self):
        self._audio_stream = self._pyaudio_if.open(
            format=pyaudio.paInt16,
            channels=self.audio_channels,
            rate=self.audio_rate,
            frames_per_buffer=1024,
            input=True)
        self._audio_buffers = []

    def _stop_recording(self):
        if hasattr(self, '_audio_stream'):
            # Stop and close the stream
            self._audio_stream.stop_stream()
            self._audio_stream.close()
            del self._audio_stream

    def _poll_audio(self):
        self._audio_buffers.append(self._audio_stream.read(1024))

    def unload(self):
        self._pyaudio_if.terminate()

    def _run(self, exp_win, ctl_win):
        self._start_recording()
        for _ in utils.wait_until_yield(
            self.task_timer,
            self.initial_wait,
            keyboard_accuracy=.05):
            self._poll_audio()

        for flip_idx, _ in enumerate(utils.wait_until_yield(
            self.task_timer,
            self.max_duration - self.final_wait,
            keyboard_accuracy=.005)):
            self._poll_audio()
            self.progress_bar.n = int(self.task_timer.getTime())
            self.progress_bar.refresh()
            if len(event.getKeys(self.done_key)):
                break
            if flip_idx < 2:
                for stim in self.fixation:
                    stim.draw(exp_win)
                yield True
            yield

        print(f"{'*'*25} PREPARE TO STOP {'*'*25}")
        for flip_idx,_ in enumerate(utils.wait_until_yield(
            self.task_timer,
            self.task_timer.getTime() + self.final_wait,
            keyboard_accuracy=.05)):
            self._poll_audio()
            yield flip_idx < 2

        print(f"{'#'*25} STOP SCANNER {'#'*25}")

    def _stop(self, exp_win, ctl_win):
        #self._mic.stop()
        self._stop_recording()
        yield True


    def _save(self):
        if hasattr(self, '_audio_buffers'):
            self.output_wav_file = self._generate_unique_filename("audio", "wav")
            wf = wave.open(self.output_wav_file, 'wb')
            wf.setnchannels(self.audio_channels)
            wf.setsampwidth(self._pyaudio_if.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.audio_rate)
            wf.writeframes(b''.join(self._audio_buffers))
            wf.close()


class FreeRecall(AudioRecording):

    INSTRUCTION_DURATION = 10

    DEFAULT_INSTRUCTION = """
Please provide an account of what you heard.
Remember you have as much time as you need.

Please provide as many details as you can.
Please try to keep your head as still as possible while you talk.

Please start talking only when the fixation dot appears.
Press A when done.
    """



class RecencyJudgments(Task):
    """docstring for RecencyJudgments."""


    DEFAULT_INSTRUCTION = """
Please choose which of the two fragments came first.
If you are unsure, choose the best possible answer.
Use up/down buttons to answer.
"""

    QUESTIONS = [
        "I like this story.",
        "I could hear and understand the story well.",
        "I can relate to the storyteller.",
        "The story was engaging",
        ]

    def __init__(
        self,
        design_file,
        initial_wait=4, final_wait=9, trial_duration_min=4, trial_duration_max=12, isi_fixation=1.5,
        run_feedback_duration=3,
        *args, **kwargs):
        super().__init__(**kwargs)
        self.initial_wait, self.final_wait = initial_wait, final_wait
        self.trial_duration_min, self.trial_duration_max, self.isi_fixation = trial_duration_min, trial_duration_max, isi_fixation
        self.run_feedback_duration = run_feedback_duration
        if not os.path.exists(design_file):
            raise ValueError(f"{design_file} does not exists")
        self.design_file = design_file
        self.design = data.importConditions(self.design_file)
        #self.design = self.design[:3]
        self.duration = len(self.design)
        self._progress_bar_refresh_rate = None

    def _setup(self, exp_win):


        self.text1 = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=1.8,
            pos=(0, .5),
        )

        self.text2 = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            wrapWidth=1.6,
            pos=(0, -.5),
        )

        self.fixation = fixation_dot(exp_win)

        # create trial handler
        self._restart()

    def _restart(self):
        self.trials = data.TrialHandler(self.design, 1, method="random")


    def _fixation(self, exp_win, offset):
        for flip, _ in enumerate(utils.wait_until_yield(
            self.task_timer,
            offset-1/(config.FRAME_RATE+1),
            keyboard_accuracy=.1)):
            if flip < 2:
                for stim in self.fixation:
                    stim.draw(exp_win)
                yield True


    def _handle_controller_presses(self, exp_win):
        self._new_key_pressed = event.getKeys('udlra')

    def _run(self, exp_win, ctl_win):
        # initial wait with fixation
        yield from self._fixation(exp_win, self.initial_wait)

        n_correct_answer = 0
        text_stims = [self.text1, self.text2]
        # trials
        for trial_n, trial in enumerate(self.trials):

            self.progress_bar.set_description(
                f"Trial {trial_n}:"
            )
            self.progress_bar.update(1)
            responses = 'AB'
            # randomize screen position
            responses = random.sample(responses, 2)

            response_keys = {k:r for k,r in zip('ud', responses)}
            # display segments
            self.text1.text = trial[f'Segment_{responses[0]}']
            self.text2.text = trial[f'Segment_{responses[1]}']
            for flip in range(2):
                for stim in text_stims:
                    stim.color = 'white'
                    stim.draw(exp_win)
                yield True
                if flip == 0:
                    trial['onset'] = self._exp_win_last_flip_time - self._exp_win_first_flip_time
            # wait for response key
            event.getKeys(response_keys.keys()) # flush keys
            for _ in utils.wait_until_yield(
                self.task_timer,
                self.task_timer.getTime() + self.trial_duration_max,
                keyboard_accuracy=.0001):
                keys = event.getKeys(response_keys.keys(), timeStamped=self.task_timer)

                if len(keys):
                    # stop on first press so there should be a single pressed key
                    key = keys[0]
                    trial['response'] = response_keys[key[0]]
                    trial['response_correct'] = trial['response'] == trial['Correct_Answer']
                    trial['response_onset'] = key[1]
                    trial['response_time'] = key[1] - trial['onset']

                    n_correct_answer += trial['response_correct']

                    chosen_idx = responses.index(trial['response'])
                    text_stims[chosen_idx].color = 'black'
                    for flip in range(2):
                        for stim in text_stims:
                            stim.draw(exp_win)
                        yield True
                    # wait for onset + min duration if answered before min duration
                    if self.task_timer.getTime() < trial['onset'] + self.trial_duration_min:
                        yield from utils.wait_until_yield(
                            self.task_timer,
                            trial['onset'] + self.trial_duration_min,
                            keyboard_accuracy=.0001)
                    break
                yield

            # flip to get screen clear timing
            yield True
            trial['offset'] = self._exp_win_last_flip_time - self._exp_win_first_flip_time
            # inter-trial fixation
            yield from self._fixation(exp_win, trial['offset'] + self.isi_fixation)


        if self.run_feedback_duration > 0:
            self.text1.color = 'white'
            self.text1.text = f"You got {n_correct_answer}/{len(self.design)} answers correct."
            self.text1.draw(exp_win)
            yield True
            yield from utils.wait_until_yield(
                self.task_timer,
                trial['offset'] + self.run_feedback_duration,
                keyboard_accuracy=.0001)

        # display questionnaire
        self.progress_bar.set_description("Questions:")
        yield from self._questionnaire(exp_win, ctl_win, [(k, q, 5) for k, q in enumerate(self.QUESTIONS)])

        # depends if questionnaire was shown
        final_wait = (
            trial['offset'] + self.run_feedback_duration + self.final_wait
            if not len(self._events) else
            self._events[-1]['onset'] + self.final_wait
            )
        # final_wait with fixation
        print(f"{'*'*25} PREPARE TO STOP {'*'*25}")
        yield from self._fixation(exp_win, final_wait)
        print(f"{'#'*25} STOP SCANNER    {'#'*25}")


    def _questionnaire(self, exp_win, ctl_win, questions):
        event.getKeys('udlra') # flush keys

        if questions is None:
            return
        exp_win.setColor([0] * 3, colorSpace='rgb')
        lines = []
        bullets = []
        responses = []
        texts = []
        legends = []
        y_spacing = 80
        win_width = exp_win.size[0]
        scales_block_x = win_width * 0.25
        scales_block_y = len(questions) // 2 * y_spacing
        extent = win_width * 0.2

        # add legends to Likert scale
        legends.append(visual.TextStim(
            exp_win,
            text = 'Disagree',
            units="pix",
            pos=(scales_block_x - extent*0.75, scales_block_y*1.4),
            wrapWidth= win_width * 0.5,
            height= y_spacing / 3,
            anchorHoriz="right",
            alignText="right",
            bold=True
        ))
        legends.append(visual.TextStim(
            exp_win,
            text = 'Agree',
            units="pix",
            pos=(scales_block_x + extent*1.15, scales_block_y*1.4),
            wrapWidth= win_width * 0.5,
            height= y_spacing / 3,
            anchorHoriz="right",
            alignText="right",
            bold=True
        ))


        active_question = 0

        # create all stimuli
        #all_questions_text = ""
        for q_n, (key, question, n_pts) in enumerate(questions):
            default_response = n_pts // 2
            responses.append(default_response)
            x_spacing = extent * 2 / (n_pts - 1)
            #all_questions_text += question + "\n\n"

            y_pos = scales_block_y - q_n * y_spacing

            lines.append(
                visual.Line(
                    exp_win,
                    (scales_block_x - extent, y_pos),
                    (scales_block_x + extent, y_pos),
                    units="pix",
                    lineWidth=6,
                    autoLog=False,
                    lineColor=(0, -1, -1) if q_n == 0 else (-1, -1, -1),
                )
            )
            bullets.append(
                [
                    visual.Circle(
                        exp_win,
                        units="pix",
                        radius=10,
                        pos=(
                            scales_block_x - extent + i * x_spacing,
                            y_pos,
                        ),
                        fillColor= (1, 1, 1) if default_response == i else (-1, -1, -1),
                        lineColor=(-1, -1, -1),
                        lineWidth=10,
                        autoLog=False,
                    )
                    for i in range(n_pts)
                ]
            )
            texts.append(visual.TextStim(
                exp_win,
                text = question,
                units="pix",
                bold = q_n == active_question,
                pos=(0, y_pos),
                wrapWidth= win_width * 0.5,
                height= y_spacing / 3,
                anchorHoriz="right",
                alignText="right"
            ))
            responses[q_n] = default_response



        # questionnaire interaction loop
        n_flips = 0
        while True:
            self._handle_controller_presses(exp_win)
            new_key_pressed = [k[0] for k in self._new_key_pressed]
            if "u" in new_key_pressed and active_question > 0:
                active_question -= 1
            elif "d" in new_key_pressed and active_question < len(questions)-1:
                active_question += 1
            elif "r" in new_key_pressed and responses[active_question] < n_pts - 1:
                responses[active_question] += 1
            elif "l" in new_key_pressed and responses[active_question] > 0:
                responses[active_question] -= 1
            elif "a" in new_key_pressed:
                for (key, question, n_pts), value in zip(questions, responses):
                    self._log_event({
                        "trial_type": "questionnaire-answer",
                        "question": key,
                        "value": value
                    })
                break
            elif n_flips > 1:
                time.sleep(.01)
                continue

            if n_flips > 0: #avoid double log when first loading questionnaire
                self._log_event({
                    "trial_type": "questionnaire-value-change",
                    "question": questions[active_question][0],
                    "value": responses[active_question]
                })

            exp_win.logOnFlip(
                level=logging.EXP,
                msg="questions %s" % responses)
            for q_n, (txt, line, bullet_q) in enumerate(zip(texts, lines, bullets)):
                #txt.bold = q_n == active_question
                txt._pygletTextObj.set_style('bold', q_n == active_question)
                line.lineColor = (0, -1, -1) if q_n == active_question else (-1, -1, -1)
                for bullet_n, bullet in enumerate(bullet_q):
                    bullet.fillColor = (1, 1, 1) if responses[q_n] == bullet_n else (-1, -1, -1)

            for stim in lines + sum(bullets, []) + texts + legends:
                stim.draw(exp_win)
            yield True
            n_flips += 1


    def _save(self):
        out_fname = self._generate_unique_filename("events", "tsv")
        self.trials.saveAsWideText(out_fname)
        events_df = pandas.read_csv(out_fname, sep="\t")
        events_df = pandas.concat([events_df, pandas.DataFrame(self._events)])
        events_df.to_csv(out_fname, sep="\t", index=False)
        return False
