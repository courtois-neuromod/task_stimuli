import os, sys, time, queue
import numpy as np
import threading

from psychopy import visual, core, data, logging, event, sound, constants
from .task_base import Task

from ..shared import config

import retro

INSTRUCTION_DURATION = 3
END_GAME_PAUSE = 3

class SoundDeviceBlockStream(sound.backend_sounddevice.SoundDeviceSound):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blocks = queue.Queue()
        self.lock = threading.Lock()

    def add_block(self, block):
        with self.lock:
            self.blocks.put(block)

    def _nextBlock(self):
        if self.status == constants.STOPPED:
            return
        if self.blocks.empty():
            block = np.zeros((self.blockSize,2),dtype=np.float)
        else:
            with self.lock:
                block = self.blocks.get()
        self.t += self.blockSize/float(self.sampleRate)
        return block

class VideoGameBase(Task):

    def _render_graphics_sound(self, obs, sound_block, exp_win, ctl_win):
        self.game_vis_stim.image = np.flip(obs,0)/255.
        self.game_vis_stim.draw(exp_win)
        self.game_vis_stim.draw(ctl_win)
        self.game_sound.add_block(sound_block[:735]/float(2**15))
        if self.game_sound.status == constants.NOT_STARTED:
            self.game_sound.play()

    def stop(self):
        self.emulator.close()
        self.game_sound.stop()

class VideoGame(VideoGameBase):

    def __init__(self,
        output_path,
        output_fname_base,
        game_name='ShinobiIIIReturnOfTheNinjaMaster-Genesis',
        state_name=None,
        *args,**kwargs):

        super().__init__(**kwargs)
        self.game_name = game_name
        self.state_name = state_name

        self.output_path = output_path
        self.output_fname_base = output_fname_base
        #self.record_dir = os.path.join(self.output_path, self.output_fname_base + '.pupil')
        #os.makedirs(self.record_dir)

    def instructions(self, exp_win, ctl_win):
        instruction_text = "Let's play a video game.\n%s : %s\nHave fun!"%(self.game_name, self.state_name)
        screen_text = visual.TextStim(
            exp_win, text=instruction_text,
            alignHoriz="center", color = 'white')

        for frameN in range(config.FRAME_RATE * INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            screen_text.draw(ctl_win)
            yield

    def preload(self, exp_win):
        self.emulator = retro.make(
            self.game_name,
            state=self.state_name,
            record=False)
        self.emulator.reset()
        movie_path = os.path.join(
            self.output_path,
            "%s_%s_%s.bk2"%(self.output_fname_base,self.game_name,self.state_name))
        logging.exp('VideoGame: recording movie in %s'%movie_path)
        self.emulator.record_movie(movie_path)
        self.game_vis_stim = visual.ImageStim(exp_win,size=exp_win.size,units='pixels',autoLog=False)
        self.game_sound = SoundDeviceBlockStream(stereo=True, blockSize=735)

    def _run(self, exp_win, ctl_win):
        # give the original size of the movie in pixels:
        #print(self.movie_stim.format.width, self.movie_stim.format.height)
        total_reward = 0
        exp_win.logOnFlip(
            level=logging.EXP,
            msg='VideoGame %s: %s starting at %f'%(self.game_name, self.state_name, time.time()))
        while True:
            # TODO: get real action from controller
            action = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            gamectrl_keys = event.getKeys('ABXYUDLR')


            _obs, _rew, _done, _info = self.emulator.step(action)
            total_reward += _rew
            if _rew > 0 :
                exp_win.logOnFlip(level=logging.EXP, msg='Reward %f'%(total_reward))

            self._render_graphics_sound(_obs,self.emulator.em.get_audio(),exp_win, ctl_win)
            yield


class VideoGameReplay(VideoGameBase):

    def __init__(self, movie_filename, game_name='ShinobiIIIReturnOfTheNinjaMaster-Genesis', *args,**kwargs):
        super().__init__(**kwargs)
        self.game_name = game_name
        self.movie_filename = movie_filename

    def instructions(self, exp_win, ctl_win):
        instruction_text = "You are going to watch someone play %s."%self.game_name
        screen_text = visual.TextStim(
            exp_win, text=instruction_text,
            alignHoriz="center", color = 'white')

        for frameN in range(config.FRAME_RATE * INSTRUCTION_DURATION):
            screen_text.draw(exp_win)
            screen_text.draw(ctl_win)
            yield

    def preload(self, exp_win):
        self.movie = retro.Movie(self.movie_filename)
        self.emulator = retro.make(
            self.game_name,
            record=False,
            state=retro.State.NONE,
            use_restricted_actions=retro.Actions.ALL,
            players=self.movie.players)
        self.emulator.initial_state = self.movie.get_state()
        self.emulator.reset()

        self.game_vis_stim = visual.ImageStim(exp_win,size=exp_win.size,units='pixels',autoLog=False)
        self.game_sound = SoundDeviceBlockStream(stereo=True, blockSize=735)

    def _run(self, exp_win, ctl_win):
        # give the original size of the movie in pixels:
        #print(self.movie_stim.format.width, self.movie_stim.format.height)
        total_reward = 0
        exp_win.logOnFlip(
            level=logging.EXP,
            msg='VideoGameReplay %s starting at %f'%(self.game_name, time.time()))
        while self.movie.step:
            keys = []
            for p in range(self.movie.players):
                for i in range(self.emulator.num_buttons):
                    keys.append(self.movie.get_key(i, p))
            _obs, _rew, _done, _info = self.emulator.step(keys)

            total_reward += _rew
            if _rew > 0 :
                exp_win.logOnFlip(level=logging.EXP, msg='Reward %f'%(total_reward))

            self._render_graphics_sound(_obs,self.emulator.em.get_audio(),exp_win, ctl_win)
            yield
