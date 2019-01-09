#!/usr/bin/python3

from psychopy import visual, logging # need to import visual first things to avoid pyglet related crash

from src.shared import config, fmri, eyetracking, cli
from src.tasks import images, video, memory, task_base, videogame

if __name__ == "__main__":
    parsed = cli.parse_args()

    all_tasks = [
        #videogame.VideoGame('./','test',state_name='Level2',name='ShinobiIIIReturnOfTheNinjaMaster-test',use_fmri=True),

        videogame.VideoGameReplay('/home/basile/data/projects/task_stimuli/test_ShinobiIIIReturnOfTheNinjaMaster-Genesis_Level2.bk2',name='ShinobiIIIReturnOfTheNinjaMaster-replay',use_fmri=True),
        task_base.Pause('We are done for today.\nWe are coming to get you out of the scanner soon.')
        ]

    cli.main_loop(all_tasks, parsed.subject, parsed.session, parsed.eyetracking, parsed.fmri)
