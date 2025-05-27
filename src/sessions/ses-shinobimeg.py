import os
import random
import retro

# point to a copy of the whole gym-retro with custom states and scenarii
retro.data.Integrations.add_custom_path(
        os.path.join(os.getcwd(), "data", "videogames", "shinobi")
)

from ..tasks import images, videogame, memory, task_base

flow_ratings = [
    ("challenge", "I feel just the right amount of challenge."),
    ("fluidity", "My thoughts/activities run fluidly and smoothly."),
    ("time","I don’t notice time passing."),
    ("focus", "I have no difficulty concentrating."),
    ("insight","My mind is completely clear."),
    ("absorption","I am totally absorbed in what I am doing."),
    ("spontaneous","The right thoughts/movements occur of their own accord."),
    ("planning", "I know what I have to do each step of the way."),
    ("control", "I feel that I have everything under control."),
    ("wandering", "I am completely lost in thought."),
]

levels_scenario = [
    ("Level1-0", "scenario_Level1"),
    ("Level4-1", "scenario_Level4-1"),
    ("Level5-0", "scenario_Level5-0")]
#random.shuffle(levels_scenario)  # randomize order

TASKS = sum(
    [
        [
            videogame.VideoGameMultiLevel(
                state_names=[l for l,s in levels_scenario],
                scenarii=[s for l,s in levels_scenario]
                ,  # this scenario repeats the same level
                repeat_scenario=True,
                max_duration=10
                * 60,  # if when level completed or dead we exceed that time in secs, stop the task
                name=f"task-shinobi_run-{run+1:02d}",
                post_level_ratings = [(k, q, 7) for k, q in flow_ratings]
            ),
            task_base.Pause(),
        ]
        for run in range(5)
    ],
    [],
)
