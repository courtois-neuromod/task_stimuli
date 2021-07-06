import time
import textwrap
import os
import pandas
from typing import List, Dict
from psychopy import visual, data, core, event
from .task_base import Task
from ..shared import config, utils

def displayText(windows: list[visual.Window], textContent: str):
    wrapWidth = config.WRAP_WIDTH

    # Deindent text content.
    textContent = textwrap.dedent(textContent)

    # For every window.
    for window in windows:
        # Ignore None.
        if window is None:
            continue
        
        # Setup text.
        # @warning used to be setup only for exp_win, then displayed on both.
        screen_obj = visual.TextStim(
            window,
            text=textContent,
            alignText="center",
            color="white",
            wrapWidth=wrapWidth,
        )

        # Display text on window.
        screen_obj.draw(window)

        # @note will be done through yield.
        window.flip(clearBuffer=True)

# @warning backbuffer isn't flipped, image wont be displayed until it is.
def drawImage(windows: list[visual.Window], image: visual.ImageStim):
    # For every window.
    for window in windows:
        # Ignore None.
        if window is None:
            continue
        
        # Draw image.
        image.draw(window)

def flipBackBuffer(windows: list[visual.Window]):
    # For every window.
    for window in windows:
        # Ignore None.
        if window is None:
            continue
        
        # Display backbuffer and clear it.
        window.flip(clearBuffer=True)

def clearScreen(windows: list[visual.Window]):
    # Clear screen
    # For every window.
    for window in windows:
        # Ignore None.
        if window is None:
            continue
        
        # Clear screen.
        window.flip(clearBuffer=True)

# Like utils.wait_until, but giving back control to the main loop event.
# @params float deadline in seconds
def waitUntil(clock: core.Clock, deadline: float):
    hogCPUperiod = 0.1
    keyboard_accuracy = .0005

    sleep_until = deadline - hogCPUperiod
    utils.poll_windows()
    current_time = clock.getTime()
    while current_time < deadline:
        # Sleep for a very short while.
        if current_time < sleep_until:
            time.sleep(keyboard_accuracy)

        # Not so sure ? Dispatch event ? Seems not relevant in our case (cf.
        # not sure pyglet is used internally).
        utils.poll_windows()

        # Update time.
        current_time = clock.getTime()

        # Give back control to main event loop.
        yield

# @note these sub-tasks don't inherit from Task (task_base), as it would
# otherwise involve the root task to override Task's base methods instead of
# overriding the `protected` (underscored) method, which are meant to be. In
# other word Task is not meant to be used in a hierarchical fashion, even
# though it is possible.
class PrismeDisplayTask():
    _fixationCross: visual.ImageStim
    _imageDir: str = None
    _runImageSetup: List[any] = None
    _preloadedImages: Dict[str, visual.ImageStim] = {}

    def __init__(self, imageDir: str, runImageSetup: List[any]):
        self._imageDir = imageDir
        self._runImageSetup = runImageSetup

    # Prefetch large files early on for accurate start with other recordings
    # (scanner, biopac...).
    def prefetch(self, exp_win: visual.Window):
        # Load fixation cross.
        fixationCrossPath = os.path.join('data', 'prisme', 'pngs',
            'fixation_cross.png')
        self._fixationCross = visual.ImageStim(exp_win, fixationCrossPath,
            size=0.5, units='deg')
        
        # Preload images.
        for currImageObj in self._runImageSetup:
            shallowImagePath = currImageObj['image_path']
            fullImagePath = os.path.join(self._imageDir, shallowImagePath)
            # @note path already has been checked within caller.
            self._preloadedImages[shallowImagePath] = visual.ImageStim(
                exp_win, fullImagePath, size=10, units='deg')

    # Run task.
    # @warning must be indempotent due to root task's #restart implementation.
    def run(self, exp_win: visual.Window, ctl_win: visual.Window):
        # Start clock.
        clock = core.Clock()

        # For each images
        for currImageObj in self._runImageSetup:
            # Draw image.
            shallowImagePath = currImageObj['image_path']
            image = self._preloadedImages[shallowImagePath]
            drawImage([exp_win, ctl_win], image)

            # Draw fixation cross. 
            drawImage([exp_win, ctl_win], self._fixationCross)

            # Display and give back control to main event loop.
            flipBackBuffer([exp_win, ctl_win])

            # Wait!
            # @warning @todo check why -1 in onset ? (I have since removed it)
            yield from waitUntil(clock, currImageObj["onset"])

        # Clear screen.
        clearScreen([exp_win, ctl_win])

        # Give back control to main loop for event handling (optional).
        yield

    def save(self):
        pass

    def teardown(self):
        pass


class PrismeMemoryTask():
    _imageDir: str = None
    _runImageSetup: List[any] = None
    _preloadedImages: Dict[str, visual.ImageStim] = {}
    _events: pandas.DataFrame = pandas.DataFrame()
    _trial: data.TrialHandler = None

    def __init__(self, imageDir: str, runImageSetup: List[any], trial: data.TrialHandler):
        self._imageDir = imageDir
        self._runImageSetup = runImageSetup
        self._trial = trial
    
    # Prefetch large files early on for accurate start with other recordings
    # (scanner, biopac...).
    def prefetch(self, exp_win: visual.Window):
        # Preload images.
        for currImageObj in self._runImageSetup:
            shallowImagePath = currImageObj['image_path']
            fullImagePath = os.path.join(self._imageDir, shallowImagePath)
            # @note path already has been checked within caller.
            self._preloadedImages[shallowImagePath] = visual.ImageStim(
                exp_win, fullImagePath, size=10, units='deg')

    # Display instructions (without any pause, in order to control for memory
    # effect induced by delay).
    def instructions(self, exp_win: visual.Window, ctl_win: visual.Window):
        duration = config.INSTRUCTION_DURATION

        # Start clock.
        clock = core.Clock()

        # Display text.
        displayText([exp_win, ctl_win], """\
            Appuyez sur le bouton correspondant à chaque image
            étant apparu lors de la séquence précédente.
            VU (bouton gauche)    NON VU (bouton droit)
        """)
        
        # Wait for the time of the instruction.
        yield from waitUntil(clock, duration)
        
        # Clear screen.
        clearScreen([exp_win, ctl_win])

        # Give back control to main loop for event handling (optional).
        yield

    # Run task.
    # @warning must be indempotent due to root task's #restart implementation.
    def run(self, exp_win: visual.Window, ctl_win: visual.Window):
        RESPONSE_KEYS = ['a','b','c','d']
        
        # Start clock.
        clock = core.Clock()

        # Clear events.
        event.clearEvents()

        # For each images
        for currImageObj in self._runImageSetup:
            # Draw image.
            shallowImagePath = currImageObj['image_path']
            image = self._preloadedImages[shallowImagePath]
            drawImage([exp_win, ctl_win], image)

            # Display and give back control to main event loop.
            flipBackBuffer([exp_win, ctl_win])

            # Wait!
            # @warning @todo check why -1 in onset ? (I have since removed it)
            print('onset:')
            print(currImageObj['onset'])
            yield from waitUntil(clock, currImageObj["onset"])
            
            # Retrieve events
            keypresses = event.getKeys(RESPONSE_KEYS, timeStamped=clock)
            
        # Clear screen.
        clearScreen([exp_win, ctl_win])

        # Give back control to main loop for event handling (optional).
        yield

    def restart(self, trial: data.TrialHandler):
        self._trial = trial

    def save(self):
        pass

    def teardown(self):
        pass

# @note the main loop is designed to run a single task every run, more task
# will lead to multiple fmri TTL awaiting in case of --fmri flag.
class PrismeTask(Task):
    # - Setup
    _displayTask: PrismeDisplayTask = None
    _memoryTask: PrismeMemoryTask = None
    _doRestart: bool = False
    _imageDir: str = None
    _runImageSetup: List[any] = None
    _trial: data.TrialHandler = None
    
    # Class constructor.
    def __init__(self, patientImageSetupPath: str, imageDir: str,
                 runIdx: int, *args, **kwargs):
        super().__init__(**kwargs)

        # Import run's image list.
        print('runIdx', runIdx)
        print('patientImageSetupPath: %s' % patientImageSetupPath)
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
        
        # Generate trial, used to store events.
        self._trial = data.TrialHandler(self._runImageSetup, 1, method="sequential")
        
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
        ], self._trial)

    # Prefetch large files early on for accurate start with other recordings
    # (scanner, biopac...).
    def _setup(self, exp_win: visual.Window):
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
    def instructions(self, exp_win: visual.Window, ctl_win: visual.Window):
        duration = config.INSTRUCTION_DURATION

        # Start clock.
        clock = core.Clock()

        # Display text.
        displayText([exp_win, ctl_win], """\
            Veuillez regardez les images durant les 5 prochaines minutes
            en essayant de ne pas bouger la tête.
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
    # @warning
    # self._doRestart within loops might be checked with a slight delay.
    def run(self, exp_win: visual.Window, ctl_win: visual.Window):
        # First run the display task, yielding back control to the main loop
        # for a bit at every step.
        displayTaskLoop = self._displayTask.run(exp_win, ctl_win)
        for idx, _ in enumerate(displayTaskLoop):
            if self._doRestart:
                break
            else:
                yield _

        # Restart the Task/Run if requested by main loop.
        if self._doRestart:
            self._doRestart = False
            return self._run(exp_win, ctl_win)

        # Then display memory task instruction and start it without a pause to
        # control for a stable delay in order to avoid the difference in delay
        # to impact person's memory and thus final result.
        memoryInstructionLoop = self._memoryTask.instructions(exp_win, ctl_win)
        for idx, _ in enumerate(memoryInstructionLoop):
            if self._doRestart:
                break
            else:
                yield _
        
        # Restart the Task/Run if requested by main loop.
        if self._doRestart:
            self._doRestart = False
            return self._run(exp_win, ctl_win)
    
        # Then run the memory task, yielding back control to the main loop
        # for a bit at every step.
        memoryTaskLoop = self._memoryTask.run(exp_win, ctl_win)
        for idx, _ in enumerate(memoryTaskLoop):
            if self._doRestart:
                break
            else:
                yield _

        # Restart the Task/Run if requested by main loop.
        if self._doRestart:
            self._doRestart = False
            return self._run(exp_win, ctl_win)


    # @note eeg spike will be sent here if --eeg flag is enabled.

    # 3rd task loop
    # `Ending` task loop, to be displayed after everything has been recorded
    # (but before events are stored, which is when the #_save method is called).
    def _stop(self, exp_win: visual.Window, ctl_win: visual.Window):
        yield

    # - Tear down

    # Override events saving if transformation are needed.
    # @returns False if events need not be saved
    def _save(self):
        self._displayTask.save()
        self._memoryTask.save()
        # @todo return True/False
        return True

    # Restart the current task, when <ctrl>-n is hit (the main loop take care
    # of listening to the event and then call this method, but doesn't do
    # anything else, such as reinstantiating the class).
    def _restart(self):
        self._doRestart = True

        # Regenerate trial, used to store events.
        self._trial = data.TrialHandler(self._runImageSetup, 1, method="sequential")
        self._memoryTask.restart(self._trial)

    # Called after everything from the task has run (including #_save).
    def unload(self):
        self._displayTask.teardown()
        self._memoryTask.teardown()
