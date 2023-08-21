import sys, os
import numpy as np
import random
import hashlib
import pandas


worlds = 8
levels = 3
exclude_list = [(2,2),(7,2)]
all_levels = [(world, level)
    for world in range(1,worlds+1)
    for level in range(1,levels+1)
    if (world,level) not in exclude_list]
n_repetitions = 50 # very high number, will never reach that point


def get_tasks(parsed):

    from ..tasks import videogame, task_base
    from .game_questionnaires import flow_ratings, other_ratings
    import json
    import retro
    # point to a copy of the whole gym-retro with custom states and scenarii
    retro.data.Integrations.add_custom_path(
            os.path.join(os.getcwd(), "data", "videogames", "mario")
    )

    bids_sub = "sub-%s" % parsed.subject

    design_path = os.path.join(
        'data',
        'videogames',
        'mario',
        "designs",
        f"{bids_sub}_design.tsv",
    )
    design = pandas.read_csv(design_path, sep='\t')
    scenario = "scenario"

    savestate_path = os.path.abspath(os.path.join(parsed.output, "sourcedata", bids_sub, f"{bids_sub}_phase-stable_task-mario_savestate.json"))

    # check for a "savestate"
    if os.path.exists(savestate_path):
        with open(savestate_path) as f:
            savestate = json.load(f)
    else:
        savestate = {"index": 0}

    for run in range(10):

        next_levels = [f"Level{world}-{level}" for idx,(world,level) in design[savestate['index']:savestate['index']+20].iterrows()]
        if len(next_levels) == 0:
            print('Stable phase completed, no more levels to play')
            return []

        task = videogame.VideoGameMultiLevel(
            game_name='SuperMarioBros-Nes',
            state_names=next_levels,
            scenarii=[scenario]*len(next_levels),
            repeat_scenario=True,
            max_duration=10 * 60,  # if when level completed or dead we exceed that time in secs, stop the task
            name=f"task-mario_run-{run+1:02d}",
            instruction="playing Super Mario Bros {state_name} \n\n Let's-a go!",
            post_run_ratings = [(k, q, 7) for k, q in enumerate(other_ratings+flow_ratings)],
            use_eyetracking=True,
            scaling=.5,
        )

        yield task

        #only increment if the task was not interrupted, if interrupted, it needs to be rescan
        if task._task_completed:
            savestate['index'] += task._nlevels
            with open(savestate_path, 'w') as f:
                json.dump(savestate, f)

        yield task_base.Pause(
            text="You can take a short break.\n Press A when ready to continue",
            wait_key='a',
        )
