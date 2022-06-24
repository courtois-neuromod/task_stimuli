import os, sys, time
from psychopy import visual, core, data, logging, sound, event
from .task_base import Task
from ..shared import config

MOVE_ON = "d"
ISI = 2

class SingleAudio(Task):

    DEFAULT_INSTRUCTION = """You are about to listen to audio stimuli"""

    INSTRUCTION_WAIT_KEY = (
        DEFAULT_INSTRUCTION + "\nWhen you're ready press <%s>" % MOVE_ON
    )

    def __init__(self, filepath, *args, **kwargs):
        self.wait_key = kwargs.pop("wait_key", False)
        super().__init__(**kwargs)
        if self.wait_key:
            self.instruction = SingleAudio.INSTRUCTION_WAIT_KEY
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

        win = visual.Window()
        
        nextFlip = win.getFutureFlipTime(clock='ptb')
        #recording.play()
        recording.play(when=nextFlip)  # sync with screen refresh

        win.flip()
        event.waitKeys()

    def _save(self):
        self.trials.saveAsWideText(self._generate_unique_filename("events", "tsv"))
        return False