import sys, os
import numpy as np
import random
import hashlib
import pandas

MARIOSTARS_KEYSET = ["b", "y", "1", "2", "u", "d", "l", "r", "3", "4", "5", "6"]

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

    scenario = 'scenario'
    bids_sub = "sub-%s" % parsed.subject
    next_levels = [f"1Player.World1.Level1" for i in range(20)]
    for run in range(10):


        task = videogame.VideoGameMultiLevel(
            game_name='SuperMarioBros3-Nes',
            state_names=next_levels,
            scenarii=[scenario]*len(next_levels),
            repeat_scenario=True,
            max_duration=10,  # if when level completed or dead we exceed that time in secs, stop the task
            name=f"task-mario3_run-{run+1:02d}",
            instruction="playing Super Mario 3 \n\n Please fixate the dot in between repetitions!",
#            post_run_ratings = [(k, q, 7) for k, q in enumerate(other_ratings+flow_ratings)],
            use_eyetracking=True,
            fixation_duration=2,
            show_instruction_between_repetitions=False,
            bg_color=[32]*3,
            n_repeats_level=1,
            completion_fn=smb3_completion_fn,
        )
        yield task
