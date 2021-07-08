import os

PRISME_DATA_PATH = os.path.join('data', 'prisme')
IMAGE_PATH = os.path.join('data', 'things', 'images')
fmri_runs = 8

# Get task function, used by app to import the right design file and init the
# right task class.
def get_tasks(parsed):
    from ...tasks.prisme import PrismeTask

    session_design_filename = os.path.join(
        PRISME_DATA_PATH,
        'designs',
        f'sub-{parsed.subject}_ses-{parsed.session}_design.tsv',
    )
    tasks = [
        PrismeTask(session_design_filename, IMAGE_PATH, run, name=f'task-prisme_run-{run}', use_eyetracking=True)
        for run in range(1, fmri_runs + 1)
    ]
    return tasks
