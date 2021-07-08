import time
import textwrap
from psychopy import visual, core
from ...shared import config, utils

def displayText(windows, textContent):
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
def drawImage(windows, image):
    # For every window.
    for window in windows:
        # Ignore None.
        if window is None:
            continue
        
        # Draw image.
        image.draw(window)

def flipBackBuffer(windows):
    # For every window.
    for window in windows:
        # Ignore None.
        if window is None:
            continue
        
        # Display backbuffer and clear it.
        window.flip(clearBuffer=True)

def clearScreen(windows):
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
def waitUntil(clock, deadline):
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
        # Might bring the focus back to the windows in order to be sure TTL /
        # keyboard event is received by the window.
        utils.poll_windows()

        # Update time.
        current_time = clock.getTime()

        # Give back control to main event loop.
        yield

def waitFor(duration):
    clock = core.Clock()
    yield from waitUntil(clock, duration)

