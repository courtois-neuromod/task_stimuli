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
DEFAULT_INSTRUCTION = """Listen to the following tracks. After each track, you will be asked to rate how well you were able to imagine the music during silences"""
AUDITORY_IMAGERY_ASSESSMENT = ("Please rate how well you were able to imagine the music during the pauses of the music clips.", 
                               ['Not at all', '', 'Partially', '', 'I clearly imagined it'])

class Playlist(Task):
#Derived from SoundTaskBase (Narratives task)
    def __init__(self, tsv_path, initial_wait=2, question_duration = 5, **kwargs):
        super().__init__(**kwargs)

        if not os.path.exists(tsv_path):
            raise ValueError("File %s does not exists" % tsv_path)   
        else :
            self.tsv_path = tsv_path
            file = open(tsv_path, "r")
            self.playlist = pandas.read_table(file, sep=' ')
            file.close()

        self.initial_wait = initial_wait
        self.question_duration = question_duration
        self.instruction = DEFAULT_INSTRUCTION
    
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
        for _ in utils.wait_until_yield(
            self.task_timer,
            self.task_timer.getTime() + self.question_duration,
            keyboard_accuracy=.0001):   

            self._handle_controller_presses(self.ISI)
            new_key_pressed = [k[0] for k in self._new_key_pressed]

            if "r" in new_key_pressed and response < n_pts - 1:
                response += 1
            elif "l" in new_key_pressed and response > 0:
                response -= 1
            elif "a" in new_key_pressed:
                self._log_event({
                    "track": self.track_name,
                    "question": question,
                    "value": response,
                    "confirmation": "yes"
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

        else:
            self._log_event({
                    "track": self.track_name,
                    "question": question,
                    "value": response,
                    "confirmation": "no"})
            pass

        #Flush questionnaire from screen   
        yield True
    
    def _run(self, exp_win, ctl_win):
        previous_track_offset = 0
        #first bullseye
        for stim in self.fixation:
            stim.draw(exp_win)
        yield True

        for index, track in self.playlist.iterrows():
            #setup track
            track_path = track['path']
            self.track_name = os.path.split(track_path)[1]
            self.sound = sound.Sound(track_path)
            self.duration = self.sound.duration

            #initial wait (bullseye 2s) 
            for _ in utils.wait_until_yield(
                self.task_timer,
                self.initial_wait + previous_track_offset,
                keyboard_accuracy=.1):
                yield
            
            #Flush bullseye from screen before track
            yield True

            #track playing (variable timing)
            track_onset = self.task_timer.getTime(applyZero=True)
            self.sound.play()
            for _ in utils.wait_until_yield(self.task_timer,
                                            previous_track_offset + self.initial_wait + self.sound.duration,
                                            keyboard_accuracy=.1):
                yield
            
            #ensure music track has been completely played
            while self.sound.status > 0:
                pass

            #display Questionnaire (variable timing, max 5s)
            yield from self._questionnaire(exp_win, ctl_win, 
                                           question=AUDITORY_IMAGERY_ASSESSMENT[0], 
                                           answers=AUDITORY_IMAGERY_ASSESSMENT[1])
            
            #display bullseye for netx iteration
            for stim in self.fixation:
                stim.draw(exp_win)
            yield True
            
            self.playlist.at[index, 'onset']=track_onset
            previous_track_offset = self.task_timer.getTime(applyZero=True)

        self.playlist.to_csv(self.tsv_path, sep=' ', index=False)

        #self.save()