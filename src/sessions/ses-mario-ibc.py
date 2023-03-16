import os
import random
import retro
import json

# point to a copy of the whole gym-retro with custom states and scenarii
retro.data.Integrations.add_custom_path(
        os.path.join(os.getcwd(), "data", "videogames", "mario")
)

from psychopy import logging
from ..tasks import images, videogame, memory, task_base

scenario = "scenario"

exclude_list = [(2,2),(7,2)] # all levels 4 are excluded below

all_levels = [(world, level) for world in range(1, 9) for level in range(1,4) if (world, level) not in exclude_list]

# code adaptive design for learning phase

def get_tasks(parsed):

    from ..tasks import videogame, task_base
    from .game_questionnaires import flow_ratings, other_ratings
    import json
    import retro
    # point to a copy of the whole gym-retro with custom states and scenarii
    retro.data.Integrations.add_custom_path(
            os.path.join(os.getcwd(), "data", "videogames", "mario")
    )

    scenario = "scenario"
    bids_sub = "sub-%s" % parsed.subject
    savestate_path = os.path.abspath(os.path.join(parsed.output, "sourcedata", bids_sub, f"{bids_sub}_phase-stable_task-mario_savestate.json"))

    # check for a "savestate"
    if os.path.exists(savestate_path):
        with open(savestate_path) as f:
            savestate = json.load(f)
    else:
        savestate = {"index": 0}

    stop_savestate = savestate.get('stop_savestate', None)
    for run in range(10):

        next_levels = [f"Level{world}-{level}" for world,level in all_levels[savestate['index']:savestate['index']+20]]
        if stop_savestate:
            next_levels = [stop_savestate] + next_levels
        if len(next_levels) == 0:
            print('All levels completed, no more levels to play')
            return []

        task = videogame.VideoGameMultiLevel(
            game_name='SuperMarioBros-Nes',
            state_names=next_levels,
            scenarii=[scenario]*len(next_levels),
            repeat_scenario=True,
            max_duration=10,  # if when level completed or dead we exceed that time in secs, stop the task
            name=f"task-mario_run-{run+1:02d}",
            instruction="playing Super Mario Bros {state_name} \n\n Let's-a go!",
            n_repeats_level=100, # very high value to repeat until success within run
            hard_run_duration_limit=True,
            fixation_duration=2,
        )

        yield task

        stop_savestate = task.stop_state_outfile
        #only increment if the task was not interrupted, if interrupted, it needs to be rescan
        if task._task_completed:
            savestate['index'] += task._nlevels
        savestate['stop_savestate'] = stop_savestate
        with open(savestate_path, 'w') as f:
            json.dump(savestate, f)

        yield task_base.Pause(
            text="You can take a short break.\n Press A when ready to continue",
            wait_key='a',
        )
