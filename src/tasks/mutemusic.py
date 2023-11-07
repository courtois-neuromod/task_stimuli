import os, time, pandas

from psychopy import prefs
prefs.hardware['audioLib'] = ['sounddevice']
from psychopy import visual, sound, event, core, logging

from .task_base import Task
from ..shared import config, utils
from ..shared.eyetracking import fixation_dot

#task : 1 run = 1 playlist = around 10 audio tracks
#repeat for n songs in subXX_runXX.csv :
#   step 1: DEFAULT_INSTRUCTION
#   step 2: display audio
#   step 3: Auditory imagery assessment
#   step 4: Familiarity assessment

#Global Variables if multiples tasks
INSTRUCTION_DURATION = 3
DEFAULT_INSTRUCTION = """Listen to the following tracks"""
AUDITORY_IMAGERY_ASSESSMENT = ("During the silences, did you imagine the missing part of the music clip you’ve heard ?", ['No', '', 'Partially', '', 'Yes'])

class Playlist(Task):
#Derived from SoundTaskBase (Narratives task)
    def __init__(self, tsv_path, initial_wait=2, final_wait=0, **kwargs):
        super().__init__(**kwargs)

        if not os.path.exists(tsv_path):
            raise ValueError("File %s does not exists" % tsv_path)   
        else :
            file = open(tsv_path, "r")
            self.playlist = pandas.read_table(file, sep='\t')
            file.close()

        self.initial_wait, self.final_wait = initial_wait, final_wait
    
    def _instructions(self, exp_win, ctl_win):
        print(self.instruction)
        screen_text = visual.TextStim(
            exp_win,
            text=self.instruction,
            alignText="center",
            color="white",
            units='height',
            height=0.05
        )
        screen_text.draw(exp_win)
        if ctl_win:
            screen_text.draw(ctl_win)
        yield True
        time.sleep(INSTRUCTION_DURATION)
        yield True

    def _setup(self, exp_win):
        super()._setup(exp_win)
        self.fixation = fixation_dot(exp_win)

    def _handle_controller_presses(self, ISI):
        ISI.start(0.01)
        self._new_key_pressed = event.getKeys('lra')
        ISI.complete()

    def _questionnaire(self, exp_win, ctl_win, question, answers):
        event.getKeys('lra') # flush keys
        self.ISI = core.StaticPeriod(win=exp_win)
        n_pts = len(answers)
        legends = []
        default_response = n_pts // 2
        response = default_response

        exp_win.setColor([0] * 3, colorSpace='rgb')
        win_width = exp_win.size[0]
        y_spacing=80
        scales_block_x = win_width * 0.25
        scales_block_y = exp_win.size[1] * 0.1
        extent = win_width * 0.2
        x_spacing= (scales_block_x  + extent) * 2 / (n_pts - 1)
        y_pos = scales_block_y - y_spacing

        #----------setup-Questionnaire-------------------------
        line = visual.Line(
                exp_win,
                (-(scales_block_x + extent), y_pos),
                (scales_block_x + extent, y_pos),
                units="pix",
                lineWidth=6,
                autoLog=False,
                lineColor=(-1, -1, -1)
            )
        
        bullets = [
                visual.Circle(
                    exp_win,
                    units="pix",
                    radius=10,
                    pos=(
                        - (scales_block_x + extent) + i * x_spacing,
                        y_pos,
                        ),
                    fillColor= (1, 1, 1) if default_response == i else (-1, -1, -1),
                    lineColor=(-1, -1, -1),
                    lineWidth=10,
                    autoLog=False,
                )
                for i in range(n_pts)
            ]

        legends = [
            visual.TextStim(
                exp_win,
                text = answer,
                units="pix",
                pos=(-(scales_block_x + extent) + i * x_spacing, exp_win.size[1] * 0.1),
                wrapWidth= win_width * 0.12,
                height= y_spacing / 4.5,
                anchorHoriz="center",
                alignText="center",
                bold=True
            )
            for i, answer in enumerate(answers)
        ]

        text = visual.TextStim(
            exp_win,
            text = question,
            units="pix",

            pos=(-(scales_block_x + extent), 
                    y_pos + exp_win.size[1] * 0.30),
            wrapWidth= win_width-(win_width*0.1),
            height= y_spacing / 3,
            anchorHoriz="left",
            alignText="left"
        )
        #---run-Questionnaire--------------------------------------

        n_flips = 0
        while True:
            self._handle_controller_presses(self.ISI)
            new_key_pressed = [k[0] for k in self._new_key_pressed]

            if "r" in new_key_pressed and response < n_pts - 1:
                response += 1
            elif "l" in new_key_pressed and response > 0:
                response -= 1
            elif "a" in new_key_pressed:
                self._events.append({
                    "track": self.track_name,
                    "question": question,
                    "value": answers[response]
                })
                break

            elif n_flips > 1:
                time.sleep(.01)
                continue

            exp_win.logOnFlip(
                level=logging.EXP,
                msg="questions %s" % response)

            for bullet_n, bullet in enumerate(bullets):
                bullet.fillColor = (1, 1, 1) if response == bullet_n else (-1, -1, -1)
            
            line.draw(exp_win)
            text.draw(exp_win)
            for legend, bullet in zip(legends, bullets):
                legend.draw(exp_win)
                bullet.draw(exp_win)
            yield True

            n_flips += 1          
    yield True
    def _run(self, exp_win, ctl_win):
        
        for stim in self.fixation:
            stim.draw(exp_win)
        yield True

        for index, track in self.playlist.iterrows():
            print(index)
            track_path = track['path']
            track_onset = float(track['onset'])
            self.track_name = os.path.split(track_path)[1]
            self.sound = sound.Sound(track_path)
            self.duration = self.sound.duration

            for _ in utils.wait_until_yield(
                self.task_timer,
                self.initial_wait + track_onset,
                keyboard_accuracy=.1):
                yield
     yield True
            self.sound.play()
            for _ in utils.wait_until_yield(self.task_timer,
                                            self.initial_wait + self.sound.duration + track_onset,
                                            keyboard_accuracy=.1):
                yield
            while self.sound.status > 0:
                pass

            for stim in self.fixation:
                stim.draw(exp_win)
            yield True

            yield from self._questionnaire(exp_win, ctl_win, 
                                           question=AUDITORY_IMAGERY_ASSESSMENT[0], 
                                           answers=AUDITORY_IMAGERY_ASSESSMENT[1])

            #imagery_form = Questionnaire(exp_win,self._events, 
                                         #trial_type='IMAGERY', name=track_name, 
                                         #question=AUDITORY_IMAGERY_ASSESSMENT[0], 
                                         #answers=AUDITORY_IMAGERY_ASSESSMENT[1])
            #imagery_form.run()  

        #self.save()