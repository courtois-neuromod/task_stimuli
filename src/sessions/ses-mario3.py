import sys, os
import numpy as np
import random
import hashlib
import pandas


def selected_levels():

    all_levels =  (
        [(1, f"Level{lev}") for lev in range(1,5)] + [(1, 'Fortress')]+[(1, f"Level{lev}") for lev in range(5,7)] + [(1, 'Airship')] +
        [(2, f"Level{lev}") for lev in range(1,3)] + [(2, 'Fortress')]+[(2, f"Level{lev}") for lev in range(3,6)] + [(2, 'Airship')] +
        [(3, f"Level{lev}") for lev in range(1,4)] + [(3, 'Fortress1')]+[(3, f"Level{lev}") for lev in range(4,8)] + [(3, 'Fortress2')]+[(3, f"Level{lev}") for lev in range(8,10)] + [(3, 'Airship')] +
        [(4, f"Level{lev}") for lev in range(1,4)] + [(4, 'Fortress1')]+[(4, f"Level{lev}") for lev in range(4,7)] + [(4, 'Fortress2'), (4, 'Airship')] +
        [(5, f"Level{lev}") for lev in range(1,4)] + [(5, 'Fortress1'), (5, 'Tower')]+[(5, f"Level{lev}") for lev in range(4,8)] + [(5, 'Fortress2')] + [(5, f"Level{lev}") for lev in range(8,10)]  + [(5, 'Airship')] +
        [(6, f"Level{lev}") for lev in range(1,4)] + [(6, 'Fortress1')]+[(6, f"Level{lev}") for lev in range(4,8)] + [(6, 'Fortress2')] + [(6, f"Level{lev}") for lev in range(8,11)]  + [(6, 'Fortress3'), (6, 'Airship')] +
        [(7, f"Level{lev}") for lev in range(1,6)] + [(7, 'PiranhaPlant1'), (7, 'Fortress1')]+[(7, f"Level{lev}") for lev in range(6,10)] + [(7, 'Fortress2'), (7, 'PiranhaPlant2'), (7, 'Airship')] +
        [(8, f"Level{lev}") for lev in range(1,3)] + [(8, 'Fortress')])
    return all_levels
    #return [lev for lev in all_levels if not 'Piranha' in lev[1]]

worlds = 1
levels = 1
exclude_list = [(2,2),(7,2)]
all_levels = [(world, level)
    for world in range(1,worlds+1)
    for level in range(1,levels+1)
    if (world,level) not in exclude_list]
n_repetitions = 9

MARIOSTARS_KEYSET = ["b", "y", "1", "2", "u", "d", "l", "r", "3", "4", "5", "6"]

def generate_design_file(subject):

    seed = int(
        hashlib.sha1(("%s" % (subject)).encode("utf-8")).hexdigest(), 16
    ) % (2 ** 32 - 1) + 42 # add a fixed offset for the designs to differ from mario phase2
    print("seed", seed)
    random.seed(seed)

    subject_levels = selected_levels() + sum([random.sample(selected_levels(),len(all_levels)) for rep in range(n_repetitions)],[])
    subject_design = pandas.DataFrame(subject_levels, columns=('world','level'))
    out_fname = os.path.join(
        'data',
        'videogames',
        'mario3',
        "designs",
        f"sub-{subject}_design.tsv",
    )
    subject_design.to_csv(out_fname, sep="\t", index=False)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="generate design files for participant / session",
    )
    parser.add_argument("subject", type=str, help="participant id")
    parsed = parser.parse_args()
    generate_design_file(parsed.subject)

def get_tasks(parsed):

    from ..tasks import videogame, task_base
    from ..tasks import videogame, task_base
    from .game_questionnaires import flow_ratings, other_ratings
    import json
    import retro
    # point to a copy of the whole gym-retro with custom states and scenarii
    retro.data.Integrations.add_custom_path(
            os.path.join(os.getcwd(), "data", "videogames", "mario3")
    )

    def smb3_completion_fn(env):
        return env.data['killed'] == 0

    bids_sub = "sub-%s" % parsed.subject

    design_path = os.path.join(
        'data',
        'videogames',
        'mario3',
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

        next_levels = [f"1Player.World{world}.{level}" for idx,(world,level) in design[savestate['index']:savestate['index']+20].iterrows()]

        task = videogame.VideoGameMultiLevel(
            game_name='SuperMarioBros3-Nes',
            state_names=next_levels,
            scenarii=[scenario]*len(next_levels),
            repeat_scenario=True,
            max_duration=7 * 60,  # if when level completed or dead we exceed that time in secs, stop the task
            name=f"task-mariostars_run-{run+1:02d}",
            instruction="playing Super Mario 3 \n\n Please fixate the dot in between repetitions!",
            post_run_ratings = [(k, q, 7) for k, q in enumerate(other_ratings+flow_ratings)],
            use_eyetracking=True,
            fixation_duration=2,
            show_instruction_between_repetitions=False,
            bg_color=[32]*3,
            n_repeats_level=3,
            completion_fn=smb3_completion_fn,
        )

        yield task

        #only increment if the task was not interrupted, if interrupted, it needs to be rescan
        if task._task_completed:
            print('saving savestate')
            savestate['index'] += task._nlevels
            with open(savestate_path, 'w') as f:
                json.dump(savestate, f)

def get_config(parsed):
    return {
        'eyetracking_calibration_version': 2,
        'eyetracking_validation': True,
        'add_pauses': True,
        'output_dataset': 'mario3',
    }
