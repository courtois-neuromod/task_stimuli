
from ..tasks import images, videogame, memory, task_base

TASKS = sum([

    [videogame.VideoGameMultiLevel(
        state_names=['Level1-0','Level4-1','Level5-0'],
        scenarii=['data/videogames/%s.json'%sc for sc in  ['scenario_repeat1', 'scenario_Level4-1', 'scenario_Level5-1']], # this scenario repeats the same level
        repeat_scenario=True,
        max_duration=10*60, # if when level completed or dead we exceed that time in secs, stop the task
        name=f"shinobi-3levels-{run+1:02d}"),
        task_base.Pause()]
    for run in range(5)

],[])
