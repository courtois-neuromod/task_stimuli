from ..tasks import retinotopy

TASKS = [
    retinotopy.Retinotopy(
        condition = condition,
        name=f"task-retinotopy{condition}",
    ) for condition in ['RETEXP','RETCON','RETCCW','RETCW','RETBAR']
]
