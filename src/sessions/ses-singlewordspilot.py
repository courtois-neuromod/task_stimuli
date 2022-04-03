
N_RUNS_PER_SESSION = 1
TRIPLET_DATA_PATH = "data/language/triplets"

def get_tasks(parsed):
    from ..tasks import language, task_base
    TASKS = [
        language.WordFeatures(
            f"{TRIPLET_DATA_PATH}/words_designs/sub-{parsed.subject}_ses-pilot{parsed.session}_run-{run+1:02d}_design.tsv",
            name="task-singlewords",
            use_eyetracking=True,
        )
        for run in range(N_RUNS_PER_SESSION)
    ]
    return TASKS
