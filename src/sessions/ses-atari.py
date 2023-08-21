import os
import random
import retro
import json

retro.data.Integrations.add_custom_path(
        os.path.join(os.getcwd(), "data", "videogames")
)

from ..tasks import images, videogame, memory, task_base

TASKS = [
            videogame.VideoGameMultiLevel(
                game_name='SpaceInvaders-Atari2600',
                state_names=["Start"],
                scenarii=['scenario']
                ,  # this scenario repeats the same level
                repeat_scenario=True,
                max_duration=10
                * 60,  # if when level completed or dead we exceed that time in secs, stop the task
                name=f"task-spaceinvaders",
                instruction="Let's play SpaceInvaders",
                # post_level_ratings = [(q, 7) for q in flow_ratings]
            ),
    ]
