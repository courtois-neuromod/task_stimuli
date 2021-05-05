import os
import random
import retro

# point to a copy of the whole gym-retro with custom states and scenarii
retro.data.Integrations.add_custom_path(
        os.path.join(os.getcwd(), "data", "videogames", "mario")
)

from ..tasks import images, videogame, memory, task_base

flow_ratings = [
    "I feel just the right amount of challenge.",
    "My thoughts/activities run fluidly and smoothly.",
    "I don’t notice time passing.",
    "I have no difficulty concentrating.",
    "My mind is completely clear.",
    "I am totally absorbed in what I am doing.",
    "The right thoughts/movements occur of their own accord.",
    "I know what I have to do each step of the way.",
    "I feel that I have everything under control.",
    "I am completely lost in thought.",
]

levels_scenario = [
    ("Level1-1", "scenario"),
    ("Level1-2", "scenario"),
    ("Level1-3", "scenario")]
#random.shuffle(levels_scenario)  # randomize order

TASKS = sum(
    [
        [
            videogame.VideoGameMultiLevel(
                game_name='SuperMarioBros-Nes',
                state_names=[l for l,s in levels_scenario],
                scenarii=[s for l,s in levels_scenario]
                ,  # this scenario repeats the same level
                repeat_scenario=True,
                max_duration=10
                * 60,  # if when level completed or dead we exceed that time in secs, stop the task
                name=f"task-supermariobros_run-{run+1:02d}",
                # post_level_ratings = [(q, 7) for q in flow_ratings]
            ),
            task_base.Pause(),
        ]
        for run in range(5)
    ],
    [],
)
