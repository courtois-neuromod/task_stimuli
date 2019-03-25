
from ..tasks import images, videogame, memory, task_base

TASKS = [

    videogame.VideoGame(state_name='Level1',name='ShinobiIIIReturnOfTheNinjaMaster-test'),
    videogame.VideoGameReplay('output/sub-test/ses-test_refactor/sub-test_ses-test_refactor_20190109_154007_ShinobiIIIReturnOfTheNinjaMaster-Genesis_Level4_000.bk2',name='ShinobiIIIReturnOfTheNinjaMaster-replay',),

]
