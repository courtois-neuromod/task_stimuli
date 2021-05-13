from ..tasks import retinotopy

TASKS = [
    retinotopy.Retinotopy(
        condition = condition,
        ncycles=4,
        name=f"task-retinotopy{condition}",
    ) for condition in ['RETRINGS','RETWEDGES','RETBAR',]#'RETCCW','RETCW','RETEXP','RETCON']
]
