from ..tasks import retinotopy
import random

conditions = ['RETWEDGES','RETRINGS','RETBAR',]
#conditions = random.shuffle(conditions)

def get_tasks(parsed):
    return [
        retinotopy.Retinotopy(
            condition = condition,
            ncycles=4,
            name=f"task-{condition[3:].lower()}",
            use_eyetracking=True,
            images_file = 'data/retinotopy/scenes.npz' if parsed.subject==6 else 'data/retinotopy/images.npz',
        ) for condition in conditions
    ]
