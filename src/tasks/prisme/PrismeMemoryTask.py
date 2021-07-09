import time
import textwrap
import os
import pandas
from psychopy import visual, data, core, logging, event
from ...shared import config, utils
from ..task_base import Task
from .utils import displayText, drawImage, flipBackBuffer, clearScreen, \
                   waitUntil, waitFor


# Does not inherit from base_task:
# otherwise involve the root task to override Task's base methods instead of
# overriding the `protected` (underscored) method, which are meant to be. In
# other word Task is not meant to be used in a hierarchical fashion, even
# though it is possible.
class PrismeMemoryTask():
    _imageDir = None
    _runImageSetup = None
    _preloadedImages = {}
    _trial = None

    # Class constructor.
    def __init__(self, imageDir, runImageSetup):
        self._imageDir = imageDir
        self._runImageSetup = runImageSetup

    # Prefetch large files early on for accurate start with other recordings
    # (scanner, biopac...).
    def prefetch(self, exp_win):
        # Preload images.
        for currImageObj in self._runImageSetup:
            shallowImagePath = currImageObj['image_path']
            fullImagePath = os.path.join(self._imageDir, shallowImagePath)
            # @note path already has been checked within caller.
            self._preloadedImages[shallowImagePath] = visual.ImageStim(
                exp_win, fullImagePath, size=10, units='deg')

    # Display instructions (without any pause, in order to control for memory
    # effect induced by delay).
    def instructions(self, exp_win, ctl_win):
        duration = config.TR * 6

        # Clear screen (optional).
        clearScreen([exp_win, ctl_win])

        # Start clock.
        clock = core.Clock()

        # Display text.
        displayText([exp_win, ctl_win], """\
            Une suite d'image va apparaître. Pour chaque image, appuyez:
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
    def run(self, exp_win, ctl_win):
        RESPONSE_KEYS = ['a','b','c','d']

        # Generate trial, used to store events.
        # @note bids spec: https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/05-task-events.html
        self._trial = data.TrialHandler(self._runImageSetup, 1, method='sequential')

        # Clear events.
        event.clearEvents()

        # Log start.
        level=logging.EXP
        msg='Prisme: memory task starting at %f' % time.time()
        exp_win.logOnFlip(level=level, msg=msg)

        # Init flip timing.
        expWinFlipTimings = {
            'start': None,
            'last_onset': None,
            'last_offset': None
        }
        exp_win.timeOnFlip(expWinFlipTimings, 'start')
        flipBackBuffer([exp_win, ctl_win])

        # Start clock.
        clock = core.Clock()

        # For each images
        for trial in self._trial:
            currImageObj = trial

            # Log next event.
            level=logging.EXP
            msg=f'image: {trial["condition"]}:{trial["image_path"]}'
            exp_win.logOnFlip(level=level, msg=msg)

            # Draw image.
            shallowImagePath = currImageObj['image_path']
            image = self._preloadedImages[shallowImagePath]
            drawImage([exp_win, ctl_win], image)

            # Wait until onset!
            # @warning @todo check why -1 in onset ? (I have since removed it).
            yield from waitUntil(clock, currImageObj['onset'])

            # Display drawn images and clear backbuffer.
            exp_win.timeOnFlip(expWinFlipTimings, 'last_onset')
            flipBackBuffer([exp_win, ctl_win])
            
            # Drop latest events from previous image (within the last 0.05s,
            # just in case).
            event.clearEvents()

            # Wait for duration.
            yield from waitFor(currImageObj['duration'])

            # Log next event.
            level=logging.EXP
            msg=f'empty screen'
            exp_win.logOnFlip(level=level, msg=msg)

            # Clear screen.
            exp_win.timeOnFlip(expWinFlipTimings, 'last_offset')
            clearScreen([exp_win, ctl_win])

            # Time backbuffer flips in order to store precise display timing.
            trial['onset_flip'] = expWinFlipTimings['last_onset'] - expWinFlipTimings['start']
            trial['offset_flip'] = expWinFlipTimings['last_offset'] - expWinFlipTimings['start']
            trial['onset_delay'] = trial['onset_flip'] - trial['onset']
            trial['duration_flip'] = trial['offset_flip'] - trial['onset_flip']

            # Wait a little further, even if the image is not longer displayed,
            # in order to avoid already sending events to the next image.
            yield from waitFor(max(0, currImageObj['pause'] - 0.05))

            # Retrieve key events.
            keypresses = event.getKeys(RESPONSE_KEYS, timeStamped=clock)
            trial['keypresses'] = keypresses
            trial['value'] = trial['keypresses']  # additional bids compatibility.
            trial['response_time'] = (keypresses[0][1] - (trial['onset'] +
                trial['onset_delay'])) if len(keypresses)>0 else None

            # Wait a little further for the last image, in order not to finish
            # the task before the last fixation cross has ended up being
            # displayed.
            isLatest = self._runImageSetup.index(currImageObj) == len(self._runImageSetup) - 1
            if isLatest:
                yield from waitFor(currImageObj['pause'])

        # Clear screen.
        clearScreen([exp_win, ctl_win])

        # Give back control to main loop for event handling (optional).
        yield

    def save(self, outputTsvPath):
        if self._trial:  # only created after instruction have been displayed.
            self._trial.saveAsWideText(outputTsvPath)

    def teardown(self):
        pass
