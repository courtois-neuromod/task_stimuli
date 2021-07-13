from ..tasks import retinotopy
import random

conditions = ['RETBAR','RETRINGS','RETWEDGES',]
#conditions = random.shuffle(conditions)

TASKS = [
    retinotopy.Retinotopy(
        condition = condition,
        ncycles=4,
        name=f"task-retinotopy{condition}",
        use_eyetracking=True,
    ) for condition in conditions #'RETCCW','RETCW','RETEXP','RETCON']
]
