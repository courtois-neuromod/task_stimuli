import os, sys, time, queue
import numpy as np
import threading

from psychopy import visual, core, data, logging, event, sound, constants
from .task_base import Task

from ..shared import config

import retro

DEFAULT_GAME_NAME = "ShinobiIIIReturnOfTheNinjaMaster-Genesis"

# KEY_SET = 'zx__abudlr_y'
# KEY_SET = 'zx__udlry___'
# KEY_SET = ['a','b','c','d','up','down','left','right','x','y','z','k']
# KEY_SET = ['x','z','_','_','up','down','left','right','c','_','_','_']
KEY_SET = ["y", "a", "_", "_", "u", "d", "l", "r", "b", "_", "_", "_"]

# KEY_SET = '0123456789'

_keyPressBuffer = []
_keyReleaseBuffer = []
import pyglet


def _onPygletKeyPress(symbol, modifier):
    if modifier:
        event._onPygletKey(symbol, modifier)
    global _keyPressBuffer
    keyTime = core.getTime()
    key = pyglet.window.key.symbol_string(symbol).lower().lstrip("_").lstrip("NUM_")
    _keyPressBuffer.append((key, keyTime))


def _onPygletKeyRelease(symbol, modifier):
    global _keyReleaseBuffer
    keyTime = core.getTime()
    key = pyglet.window.key.symbol_string(symbol).lower().lstrip("_").lstrip("NUM_")
    _keyReleaseBuffer.append((key, keyTime))


class SoundDeviceBlockStream(sound.backend_sounddevice.SoundDeviceSound):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blocks = queue.Queue()
        self.lock = threading.Lock()

    def add_block(self, block):
        with self.lock:
            self.blocks.put(block)

    def flush(self):
        with self.lock:
            self.blocks = queue.Queue()

    def _nextBlock(self):
        if self.status == constants.STOPPED:
            return
        if self.blocks.empty():
            block = np.zeros((self.blockSize, 2), dtype=np.float)
        else:
            with self.lock:
                block = self.blocks.get()
        self.t += self.blockSize / float(self.sampleRate)
        return block


class VideoGameBase(Task):

    def __init__(
        self,
        game_name=DEFAULT_GAME_NAME,
        state_name=None,
        scenario=None,
        repeat_scenario=True,
        inttype=retro.data.Integrations.CUSTOM_ONLY,
        *args,
        **kwargs
    ):

        super().__init__(**kwargs)
        self.game_name = game_name
        self.state_name = state_name
        self.scenario = scenario
        self.repeat_scenario = repeat_scenario
        self.inttype = inttype

    def _setup(self, exp_win):

        super()._setup(exp_win)

        self._first_frame = self.emulator.reset()
        first_sound_chunk = self.emulator.em.get_audio()
        blockSize = first_sound_chunk.shape[0]
        self.game_sound = SoundDeviceBlockStream(
            sampleRate = self.emulator.em.get_audio_rate(),
            stereo=(first_sound_chunk.ndim==2 & first_sound_chunk.shape[1]==2),
            blockSize=blockSize)

        min_ratio = min(
            exp_win.size[0] / self._first_frame.shape[1],
            exp_win.size[1] / self._first_frame.shape[0],
        )
        width = int(min_ratio * self._first_frame.shape[1])
        height = int(min_ratio * self._first_frame.shape[0])

        self.game_vis_stim = visual.ImageStim(
            exp_win,
            size=(width, height),
            units="pixels",
            interpolate=False,
            flipVert=True,
            autoLog=False,
        )

    def _transform_soundblock(self, sound_block):
        return sound_block[:self.game_sound.blockSize] / float(2 ** 15)

    def _render_graphics_sound(self, obs, sound_block, exp_win, ctl_win):
        self.game_vis_stim.image = obs / 255.0
        self.game_vis_stim.draw(exp_win)
        if ctl_win:
            self.game_vis_stim.draw(ctl_win)
        self.game_sound.add_block(self._transform_soundblock(sound_block))
        if not self.game_sound.status == constants.PLAYING:
            exp_win.callOnFlip(self.game_sound.play)  # start sound only at flip

    def _stop(self, exp_win, ctl_win):
        self.game_sound.stop()
        self.emulator.stop_record() # to be sure to save the bk2
        exp_win.setColor([0] * 3, colorSpace='rgb')
        if ctl_win:
            ctl_win.setColor([0] * 3, colorSpace='rgb')
        yield True

    def unload(self):
        self.emulator.close()


class VideoGame(VideoGameBase):

    DEFAULT_INSTRUCTION = "Let's play {game_name}: {state_name}\nHave fun!"

    def __init__(
        self,
        max_duration=0,
        post_level_ratings=None,
        post_run_ratings=None,
        *args,
        **kwargs
    ):

        super().__init__(**kwargs)
        self.max_duration = max_duration
        self.duration = max_duration
        self.post_level_ratings = post_level_ratings
        self.post_run_ratings = post_run_ratings
        self._completed = False

    def _instructions(self, exp_win, ctl_win):

        instruction = self.instruction.format(
            **{'game_name':self.game_name,
             'state_name':self.state_name})

        screen_text = visual.TextStim(
            exp_win,
            text=instruction,
            alignText="center",
            color="white",
            wrapWidth=config.WRAP_WIDTH,
        )

        for frameN in range(config.FRAME_RATE * config.INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield frameN < 2
        yield True

    def _setup(self, exp_win):

        retraceRate = exp_win._monitorFrameRate
        if retraceRate is None:
            retraceRate = exp_win.getActualFrameRate()
        if retraceRate is None:
            logging.warning("FrameRate could not be supplied by psychopy; "
                            "defaulting to 60.0")
            retraceRate = 60.0
        self._retraceInterval = 1.0/retraceRate

        self.emulator = retro.make(
            self.game_name,
            state=self.state_name,
            scenario=self.scenario,
            record=False,
            inttype=self.inttype
        )

        self.game_fps = self.emulator.em.get_screen_rate()
        self._frameInterval = 1.0/self.game_fps

        super()._setup(exp_win)
        self._set_recording_file()

    def _set_recording_file(self):
        nnn = 0
        while True:
            self.movie_path = os.path.join(
                self.output_path,
                "%s_%s_%s_%03d.bk2"
                % (self.output_fname_base, self.game_name, self.state_name, nnn),
            )
            if not os.path.exists(self.movie_path):
                break
            nnn += 1
        logging.exp("VideoGame: recording movie in %s" % self.movie_path)
        self.emulator.record_movie(self.movie_path)

    def _handle_controller_presses(self, exp_win):
        exp_win.winHandle.dispatch_events()
        global _keyPressBuffer, _keyReleaseBuffer

        for k in _keyReleaseBuffer:
            self.pressed_keys.discard(k[0])
            logging.data(f"Keyrelease: {k[0]}", t=k[1])
        _keyReleaseBuffer.clear()
        for k in _keyPressBuffer:
            self.pressed_keys.add(k[0])
        self._new_key_pressed = _keyPressBuffer[:] #copy
        _keyPressBuffer.clear()
        return self.pressed_keys

    def clear_key_buffers(self):
        global _keyPressBuffer, _keyReleaseBuffer
        self.pressed_keys.clear()
        _keyReleaseBuffer.clear()
        _keyPressBuffer.clear()

    def _run_emulator(self, exp_win, ctl_win):

        total_reward = 0
        _done = False
        level_step = 0
        keys = [False] * 12

        # flush all keys to avoid unwanted actions
        self.clear_key_buffers()

        # render the initial frame and audio
        self._render_graphics_sound(
            self._first_frame, self.emulator.em.get_audio(), exp_win, ctl_win
        )
        exp_win.logOnFlip(level=logging.EXP, msg="level step: %d" % level_step)
        exp_win.callOnFlip(
            self._log_event,
            {
                "trial_type": "gym-retro_game",
                "game": self.game_name,
                "level": self.state_name,
                "stim_file": self.movie_path,
            },
        )
        yield True
        _nextFrameT = self._retraceInterval
        while not _done:
            level_step += 1
            while _nextFrameT > (self.task_timer.getTime() -
                       self._retraceInterval/2.0):
                time.sleep(.0001)
            self._handle_controller_presses(exp_win)
            keys = [k in self.pressed_keys for k in KEY_SET]
            _obs, _rew, _done, self._game_info = self.emulator.step(keys)
            total_reward += _rew
            if _rew > 0:
                exp_win.logOnFlip(level=logging.EXP, msg="Reward %f" % (total_reward))
            self._render_graphics_sound(
                _obs, self.emulator.em.get_audio(), exp_win, ctl_win
            )
            if _done:
                exp_win.logOnFlip(
                    level=logging.EXP,
                    msg="VideoGame %s: %s stopped at %f"
                    % (self.game_name, self.state_name, time.time()),
                )
            if not level_step % config.FRAME_RATE:
                exp_win.logOnFlip(level=logging.EXP, msg="level step: %d" % level_step)
            yield True
            _nextFrameT += self._frameInterval
        self._completed = self._completed or self._game_info['lives'] > -1
        self.game_sound.flush()
        self.game_sound.stop()
        self.emulator.stop_record()

    def _set_key_handler(self, exp_win):
        # activate repeat keys
        exp_win.winHandle.on_key_press = _onPygletKeyPress
        exp_win.winHandle.on_key_release = _onPygletKeyRelease
        self.pressed_keys = set()

    def _unset_key_handler(self, exp_win):
        # deactivate custom keys handling
        exp_win.winHandle.on_key_press = event._onPygletKey
        # del exp_win.winHandle.on_key_release

    def _run(self, exp_win, ctl_win):

        self._set_key_handler(exp_win)
        self._nlevels = 0
        exp_win.setColor([-1.0] * 3, colorSpace='rgb')
        if ctl_win:
            ctl_win.setColor([-1.0] * 3, colorSpace='rgb')

        while True:
            self._nlevels += 1
            exp_win.logOnFlip(
                level=logging.EXP,
                msg="VideoGame %s: %s starting at %f"
                % (self.game_name, self.state_name, time.time()),
            )
            yield from self._run_emulator(exp_win, ctl_win)
            if self.post_level_ratings:
                yield from self._run_ratings(exp_win, ctl_win)
            if not self.repeat_scenario or (
                self.max_duration and self.task_timer.getTime() > self.max_duration
            ):  # stop if we are above the planned duration
                break
            self.emulator.reset()

        exp_win.setColor([0] * 3, colorSpace='rgb')
        if ctl_win:
            ctl_win.setColor([0] * 3, colorSpace='rgb')

    def _run_ratings(self, exp_win, ctl_win):
        for question, n_pts in self.post_level_ratings:
            yield from self._likert_scale_answer(exp_win, ctl_win, question, n_pts)

        text = visual.TextStim(exp_win, "Thanks for your answers", pos=(0, 0))
        for i in range(config.FRAME_RATE):
            text.draw(exp_win)
            yield i < 3
        # clear screen
        for i in range(2):
            yield True

    def _questionnaire(self, exp_win, ctl_win, questions):

        exp_win.setColor([0] * 3, colorSpace='rgb')
        if questions is None:
            return
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
            units="pixels",
            pos=(scales_block_x - extent*0.75, scales_block_y*1.1),
            wrapWidth= win_width * 0.5,
            height= y_spacing / 3,
            anchorHoriz="right",
            alignText="right",
            bold=True
        ))
        legends.append(visual.TextStim(
            exp_win,
            text = 'Agree',
            units="pixels",
            pos=(scales_block_x + extent*1.15, scales_block_y*1.1),
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
                    units="pixels",
                    lineWidth=6,
                    autoLog=False,
                    lineColor=(0, -1, -1) if q_n == 0 else (-1, -1, -1),
                )
            )
            bullets.append(
                [
                    visual.Circle(
                        exp_win,
                        units="pixels",
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
                units="pixels",
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
                        "game": self.game_name,
                        "level": self.state_name,
                        "stim_file": self.movie_path,
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
                    "game": self.game_name,
                    "level": self.state_name,
                    "stim_file": self.movie_path,
                    "question": questions[active_question][0],
                    "value": responses[active_question]
                })

            exp_win.logOnFlip(
                level=logging.EXP,
                msg="level ratings %s" % responses)
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

    def _likert_scale_answer(
        self, exp_win, ctl_win, question, n_pts=7, extent=0.6, autoLog=False
    ):
        extent *= config.EXP_WINDOW["size"][0]
        value = n_pts // 2
        answered = False
        text = visual.TextStim(exp_win, question, pos=(0, 0.5))
        line = visual.Line(
            exp_win,
            (-extent, 0),
            (extent, 0),
            units="pixels",
            lineWidth=2,
            autoLog=False,
        )
        x_spacing = extent * 2 / (n_pts - 1)
        circles = [
            visual.Circle(
                exp_win,
                units="pixels",
                radius=40,
                pos=(-extent + i * x_spacing, 0),
                fillColor=(-1, -1, -1),
                lineColor=(-1, -1, -1),
                lineWidth=10,
                autoLog=False,
            )
            for i in range(n_pts)
        ]
        circles[value].fillColor = (1, 1, 1)
        frame = 0
        while not answered:
            frame += 1
            for stim in [text, line] + circles:
                stim.draw(exp_win)
            self._handle_controller_presses(exp_win)
            if "a" in self.pressed_keys:
                exp_win.logOnFlip(
                    level=logging.EXP,
                    msg="nlevel: %d, question: %s, answer: %d"
                    % (self._nlevels, question, value),
                )
                for i in range(config.FRAME_RATE):
                    yield True
                self.pressed_keys.clear()
                break
            if "r" in self.pressed_keys and value < n_pts - 1:
                value += 1
            elif "l" in self.pressed_keys and value > 0:
                value -= 1
            else:
                yield frame < 4
                continue
            self.pressed_keys.clear()
            for c in circles:
                c.fillColor = (-1, -1, -1)
            circles[value].fillColor = (1, 1, 1)

            yield True
        yield True

    def _stop(self, exp_win, ctl_win):
        self._unset_key_handler(exp_win)
        exp_win.waitBlanking = True
        yield from super()._stop(exp_win, ctl_win)


class VideoGameMultiLevel(VideoGame):
    def __init__(self, *args, **kwargs):

        self._state_names = kwargs.pop("state_names")
        self._scenarii = kwargs.pop("scenarii")
        self._repeat_scenario_multilevel = kwargs.get("repeat_scenario", False)

        kwargs["repeat_scenario"] = False
        super().__init__(
            state_name=self._state_names[0], scenario=self._scenarii[0], **kwargs
        )

    def _run(self, exp_win, ctl_win):

        #exp_win.waitBlanking = False
        self._set_key_handler(exp_win)
        self._nlevels = 0
        while True:
            for level, scenario in zip(self._state_names, self._scenarii):
                self._nlevels += 1
                self.state_name = level
                self.emulator.load_state(level, inttype=self.inttype)
                self.emulator.data.load(
                    retro.data.get_file_path(self.game_name, "data.json", inttype=self.inttype),
                    retro.data.get_file_path(self.game_name, f"{scenario}.json", inttype=self.inttype)
                )
                self._first_frame = self.emulator.reset()
                if self._nlevels > 1:
                    self._set_recording_file()
                    yield from self._instructions(exp_win, ctl_win)

                exp_win.setColor([-1.0] * 3, colorSpace='rgb')
                if ctl_win:
                    ctl_win.setColor([-1.0] * 3, colorSpace='rgb')
                yield from super()._run_emulator(exp_win, ctl_win)
                self.game_sound.stop()

                yield from self._questionnaire(
                    exp_win, ctl_win, self.post_level_ratings
                )

                time_exceeded = (
                    self.max_duration and self.task_timer.getTime() > self.max_duration
                )
                if time_exceeded:  # stop if we are above the planned duration
                    break
            if time_exceeded or not self._repeat_scenario_multilevel:
                break
        yield from self._questionnaire(
            exp_win, ctl_win, self.post_run_ratings
        )

        #exp_win.waitBlanking = True


class VideoGameReplay(VideoGameBase):
    def __init__(
        self,
        movie_filename,
        *args,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.game_name = game_name
        self.scenario = scenario
        self.movie_filename = movie_filename
        if not os.path.exists(self.movie_filename):
            raise ValueError("file %s does not exists" % self.movie_filename)

    def instructions(self, exp_win, ctl_win):
        instruction_text = "You are going to watch someone play %s." % self.game_name
        screen_text = visual.TextStim(
            exp_win, text=instruction_text, alignText="center", color="white"
        )

        for frameN in range(config.FRAME_RATE * INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            if ctl_win:
                screen_text.draw(ctl_win)
            yield

    def _setup(self, exp_win):
        self.movie = retro.Movie(self.movie_filename)
        self.emulator = retro.make(
            self.game_name,
            record=False,
            state=retro.State.NONE,
            scenario=self.scenario,
            # use_restricted_actions=retro.Actions.ALL,
            players=self.movie.players,
        )

        self.emulator.initial_state = self.movie.get_state()
        super()._setup(exp_win)

    def _run(self, exp_win, ctl_win):
        # give the original size of the movie in pixels:
        # print(self.movie_stim.format.width, self.movie_stim.format.height)
        total_reward = 0
        exp_win.logOnFlip(
            level=logging.EXP,
            msg="VideoGameReplay %s starting at %f" % (self.game_name, time.time()),
        )
        while self.movie.step():
            keys = []
            for p in range(self.movie.players):
                for i in range(self.emulator.num_buttons):
                    keys.append(self.movie.get_key(i, p))

            _obs, _rew, _done, _info = self.emulator.step(keys)

            total_reward += _rew
            if _rew > 0:
                exp_win.logOnFlip(level=logging.EXP, msg="Reward %f" % (total_reward))

            self._render_graphics_sound(
                _obs, self.emulator.em.get_audio(), exp_win, ctl_win
            )
            yield
