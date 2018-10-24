import os, sys
from psychopy import visual, core, data

#from shared import fmri, config

FRAMERATE = 60
STIMULI_DURATION=2
ISI=4
IMAGES_FOLDER = '/home/basile/data/projects/task_stimuli/BOLD5000_Stimuli/Scene_Stimuli/Presented_Stimuli/ImageNet'

def image_task():
    experiment_window = visual.Window()

    image_names = data.importConditions('test_conditions.csv')

    instruction_text = """Please keep your eyes open an focused on the screen all the time.
You will see pictures of scenes and objects."""

    screen_text = visual.TextStim(
        experiment_window, text=instruction_text,
        alignHoriz="center", color = 'white')

    for frameN in range(FRAMERATE * STIMULI_DURATION):
        screen_text.draw()
        experiment_window.flip()

    trials = data.TrialHandler(image_names, 1, method='sequential')

    for trial in trials:
        image_path = os.path.join(IMAGES_FOLDER,trial['image_path'])
        img = visual.ImageStim(experiment_window, image_path)
        for frameN in range(FRAMERATE * STIMULI_DURATION):
            img.draw()
            experiment_window.flip()
        for frameN in range(FRAMERATE * ISI):
            experiment_window.flip()


image_task()
