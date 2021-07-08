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
class PrismeDisplayTask():
    _fixationCross = None
    _imageDir = None
    _runImageSetup = None
    _preloadedImages = {}
    _trial = None

    # Class constructor.
    def __init__(self, imageDir, runImageSetup):
        self._imageDir = imageDir
        self._runImageSetup = runImageSetup

        # Generate trial, used to store events (mainly onset/offset backbuffer
        # flip to get precise display timing).
        # @note bids spec: https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/05-task-events.html
        self._trial = data.TrialHandler(self._runImageSetup, 1, method='sequential')

    # Prefetch large files early on for accurate start with other recordings
    # (scanner, biopac...).
    def prefetch(self, exp_win):
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
    def run(self, exp_win, ctl_win):
        # Log start.
        level=logging.EXP
        msg='Prisme: display task starting at %f' % time.time()
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
            # @warning @todo check why -1 in onset ? (I have since removed it)
            yield from waitUntil(clock, currImageObj['onset'])

            # Display drawn images and clear backbuffer.
            exp_win.timeOnFlip(expWinFlipTimings, 'last_onset')
            flipBackBuffer([exp_win, ctl_win])

            # Wait for duration.
            yield from waitFor(currImageObj['duration'])

            # Log next event.
            level=logging.EXP
            msg=f'fixation'
            exp_win.logOnFlip(level=level, msg=msg)

            # Display fixation cross only and clear backbuffer.
            drawImage([exp_win, ctl_win], self._fixationCross)
            exp_win.timeOnFlip(expWinFlipTimings, 'last_offset')
            flipBackBuffer([exp_win, ctl_win])

            # Time backbuffer flips in order to store precise display timing.
            trial['onset_flip'] = expWinFlipTimings['last_onset'] - expWinFlipTimings['start']
            trial['offset_flip'] = expWinFlipTimings['last_offset'] - expWinFlipTimings['start']
            trial['onset_delay'] = trial['onset_flip'] - trial['onset']
            trial['duration_flip'] = trial['offset_flip'] - trial['onset_flip']

            # Give back control to main loop for event handling (optional).
            yield

        # Clear screen.
        clearScreen([exp_win, ctl_win])

        # Give back control to main loop for event handling (optional).
        yield

    def restart(self):
        # Generate trial, used to store events.
        self._trial = data.TrialHandler(self._runImageSetup, 1, method='sequential')

    def save(self, outputTsvPath):
        self._trial.saveAsWideText(outputTsvPath)

    def teardown(self):
        pass
