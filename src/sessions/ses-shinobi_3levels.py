from ..tasks import images, videogame, memory, task_base

TASKS = [
    videogame.VideoGame(
        state_name="Level1",
        scenario="scenario_repeat1",  # this scenario repeats the same level
        max_duration=10
        * 60,  # if when level completed or dead we exceed that time in secs, stop the task
        name="ShinobiIIIReturnOfTheNinjaMaster-level1",
    ),
    # videogame.VideoGameReplay('output/sub-test/ses-test_refactor/sub-test_ses-test_refactor_20190109_154007_ShinobiIIIReturnOfTheNinjaMaster-Genesis_Level4_000.bk2',name='ShinobiIIIReturnOfTheNinjaMaster-replay',),
    videogame.VideoGame(
        state_name="Level4-1",
        scenario="scenario_Level4-1",  # this scenario repeats the same level
        max_duration=10
        * 60,  # if when level completed or dead we exceed that time in secs, stop the task
        name="ShinobiIIIReturnOfTheNinjaMaster-level4-1",
    ),
    videogame.VideoGame(
        state_name="Level5-0",
        scenario="scenario_Level5-0",  # this scenario repeats the same level
        max_duration=10
        * 60,  # if when level completed or dead we exceed that time in secs, stop the task
        name="ShinobiIIIReturnOfTheNinjaMaster-level5-0",
    ),
] * 3  ###!!!!!!!!!!! REPEAT !!!!!!!!!!!###
