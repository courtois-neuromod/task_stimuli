import time
import textwrap
import os
import pandas
from psychopy import visual, data, core, logging, event
from ...shared import config, utils
from ..task_base import Task
from .utils import displayText, drawImage, flipBackBuffer, clearScreen, \
                   waitUntil, waitFor
from .PrismeDisplayTask import PrismeDisplayTask
from .PrismeMemoryTask import PrismeMemoryTask


# The framework main loop is designed to run a single task every run, more task
# will lead to multiple fmri TTL awaiting in case of --fmri flag. Therefore,
# as we want both our display and memory task to be shown consecutively, we use
# this main task to 'glue' them together.
class PrismeTask(Task):
    _displayTask = None
    _memoryTask = None
    _imageDir = None
    _runImageSetup = None
    
    # Class constructor.
    def __init__(self, patientImageSetupPath, imageDir,
                 runIdx, *args, **kwargs):
        super().__init__(**kwargs)

        # Import run's image list.
        patientImageSetup = data.importConditions(patientImageSetupPath)
        runImageSetup = [
            currImageObj for currImageObj in patientImageSetup
            if currImageObj['run'] == runIdx and currImageObj['type'] == 'fmri'
        ]
        
        # Ensure image exists.
        for currImageObj in runImageSetup:
            fullImagePath = os.path.join(imageDir, currImageObj['image_path'])
            if not os.path.exists(imageDir) or not \
               os.path.exists(fullImagePath):
                raise ValueError('Cannot find the listed image %s ' %
                                 fullImagePath)
        
        # Store setup.
        self._imageDir = imageDir
        self._runImageSetup = runImageSetup
        
        # Instantiate sub-tasks.
        self._displayTask = PrismeDisplayTask(self._imageDir, [
            currImageObj for currImageObj in self._runImageSetup
            if currImageObj['condition'] == 'shown'
        ])
        self._memoryTask = PrismeMemoryTask(self._imageDir, [
            currImageObj for currImageObj in self._runImageSetup
            if currImageObj['condition'] in ['neg', 'pos']
        ])

    # Prefetch large files early on for accurate start with other recordings
    # (scanner, biopac...).
    def _setup(self, exp_win):
        self._displayTask.prefetch(exp_win)
        self._memoryTask.prefetch(exp_win)

    # - Task loops

    # @note
    # The core of the software architecture is designed as a general main loop,
    # processing task and events bits by bits.
    # Any yield within the underlying sub-loops gives back software's control
    # to the main loop, thus letting inputs (such as. <ctrl>-C) be processed.
    # Once the main loop has finished its temporary job, it gives back control
    # to the python method (generator). It also record a movie frame every 6th
    # yield if --record-movie is enabled.

    # 1st task loop
    # `Awaiting` task loop, to be displayed while awaiting fmri TTL to be sent
    # (in case flag --fmri is on), before eyetracker has started recording,
    # before EEG TTL has been sent, etc etc.
    #
    # @warning
    # Other instructions such as eyetracking may already have been displayed.
    # @warning
    # Main loop seems not to contain any sleep to wait inbetween frame so
    # it's likely all frames will be run at once, and event will be
    # ignored until next frame is yield.
    # @note main loop doesn't rely on generator argument, but Task
    # (base_task) use it in order to know if it has to clear the buffer
    # after (when True) displaying the frame (by flipping the backbuffer), but
    # only when using #_instructions instead of #instructions.
    def instructions(self, exp_win, ctl_win):
        duration = config.INSTRUCTION_DURATION

        # Start clock.
        clock = core.Clock()

        # Display text.
        displayText([exp_win, ctl_win], """\
            Regardez les images durant les 5 prochaines minutes
            en gardant la tête immobile.
        """)
        
        # Wait for the time of the instruction.
        yield from waitUntil(clock, duration)
        
        # Clear screen.
        clearScreen([exp_win, ctl_win])

        # Give back control to main loop for event handling (optional).
        yield

    # @note main loop will wait for TTL here if --fmri flag is enabled.
    # @note eeg spike will be sent here if --eeg flag is enabled.
    # @note eyetracking record will start here if --eyetracking flag is enabled.

    # 2nd task loop
    # `Running` task loop, to be displayed while everything is recording (eeg,
    # eyetracker, fmri, etc).
    def run(self, exp_win, ctl_win):
        # First run the display task, yielding back control to the main loop
        # for a bit at every step.
        displayTaskLoop = self._displayTask.run(exp_win, ctl_win)
        for idx, _ in enumerate(displayTaskLoop):
            yield _

        # Add a 6 * TR padding before showing memory task' instructions in
        # order to capture late hemodynamic response.
        yield from waitFor(6 * config.TR)

        # Then display memory task instruction and start it without a pause to
        # control for a stable delay in order to avoid the difference in delay
        # to impact person's memory and thus final result.
        memoryInstructionLoop = self._memoryTask.instructions(exp_win, ctl_win)
        for idx, _ in enumerate(memoryInstructionLoop):
            yield _

        # Then run the memory task, yielding back control to the main loop
        # for a bit at every step.
        memoryTaskLoop = self._memoryTask.run(exp_win, ctl_win)
        for idx, _ in enumerate(memoryTaskLoop):
            yield _

    # @note eeg spike will be sent here if --eeg flag is enabled.

    # 3rd task loop
    # `Ending` task loop, to be displayed after everything has been recorded
    # (but before events are stored, which is when the #_save method is called).
    def _stop(self, exp_win, ctl_win):
        yield

    # - Tear down

    # Override events saving if transformation are needed.
    # @returns False if events need not be saved
    def _save(self):
        displayEventsTsvPath = self._generate_unique_filename('display_events', 'tsv')
        self._displayTask.save(displayEventsTsvPath)
        memoryEventsTsvPath = self._generate_unique_filename('memory_events', 'tsv')
        self._memoryTask.save(memoryEventsTsvPath)
        return False  # we save events ourselves, without relying on the
                      # underlying framework.

    # Restart the current task, when <ctrl>-n is hit (the main loop take care
    # of listening to the event and then call this method, but doesn't do
    # anything else, such as reinstantiating the class).
    def _restart(self):
        pass

    # Called after everything from the task has run (including #_save).
    def unload(self):
        self._displayTask.teardown()
        self._memoryTask.teardown()
