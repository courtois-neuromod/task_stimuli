from ..tasks import retinotopy
import random

conditions = ['RETWEDGES','RETRINGS','RETBAR',]
#conditions = random.shuffle(conditions)

TASKS = [
    retinotopy.Retinotopy(
        condition = condition,
        ncycles=4,
        name=f"task-{condition[3:].lower()}",
        use_eyetracking=True,
    ) for condition in conditions
]
