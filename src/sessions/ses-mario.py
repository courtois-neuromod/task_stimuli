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

from .game_questionnaires import flow_ratings

scenario = "scenario"

exclude_list = [(2,2),(7,2)] # all levels 4 are excluded below

# code adaptive design for learning phase

def get_tasks(parsed):
    bids_sub = "sub-%s" % parsed.subject
    savestate_path = os.path.abspath(os.path.join(parsed.output, "sourcedata", bids_sub, f"{bids_sub}_task-mario_savestate.json"))

    # check for a "savestate"
    if os.path.exists(savestate_path):
        with open(savestate_path) as f:
            savestate = json.load(f)
    else:
        savestate = {"world": 1, "level":1}

    for run in range(10):
        if savestate['world'] == 9:
            break
        current_level = f"Level{savestate['world']}-{savestate['level']}"
        task = videogame.VideoGameMultiLevel(
            game_name='SuperMarioBros-Nes',
            state_names=[current_level],
            scenarii=[scenario],
            repeat_scenario=False,
            max_duration=1 * 60,  # if when level completed or dead we exceed that time in secs, stop the task
            name=f"task-mario_run-{run+1:02d}",
            instruction="playing Super Mario Bros {state_name} \n\n Let's-a go!",
            post_run_ratings = [(k, q, 7) for k, q in enumerate(flow_ratings)],
            use_eyetracking=True,
        )
        yield task

        if task._completed:
            logging.exp(f"{current_level} successfuly completed at least once.")
            savestate['level'] += 1
            if savestate['level'] > 3:
                savestate['world'] +=1
                savestate['level'] = 1
            while (savestate['world'], savestate['level']) in exclude_list:
                savestate['level'] += 1
                if savestate['level'] > 3:
                    savestate['world'] +=1
                    savestate['level'] = 1
            with open(savestate_path, 'w') as f:
                json.dump(savestate, f)
        else:
            logging.exp(f"{current_level} not completed.")

        yield task_base.Pause(
            text="You can take a short break.\n Press A when ready to continue",
            wait_key='a',
        )

    #move into phase2
    print("WARNING: the player has completed PHASE1, moving into PHASE2")
    import importlib
    phase2 = importlib.import_module('src.sessions.ses-mario-phase2')
    yield from phase2.get_tasks(parsed)
