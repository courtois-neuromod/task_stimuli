from ..tasks.localizers import FLoc

#TASKS = [
#    FLoc(task='OneBack', images_sets='alternate', name='floc'),
#]

# 'Task': ['OneBack', 'TwoBack', 'Oddball'],
# 'Image Set': ['default', 'alternate', 'both']

TASKS = [
    FLoc(task='OneBack', images_sets='default', name='task-flocdef', use_eyetracking=True),
    FLoc(task='OneBack', images_sets='alternate', name='task-flocalt', use_eyetracking=True)    
]
