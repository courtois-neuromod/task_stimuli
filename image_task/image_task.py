from psychopy import visual, core

from ..global import fmri

win = visual.Window()

image_names = data.importConditions('')

instruction_text = """Please keep your eyes focused on the middle of the screen at all times.

You will see pictures of scenes and objects.
Please press the right index key for like, middle for neutral,
ring finger for dislike. Please respond after the image is shown."""

screen_text = visual.TextStim(
    experiment_window, text=instruction_text,
    alignHoriz="center", color = 'white')

trials = data.TrialHandler(image_names,20, method='random')
