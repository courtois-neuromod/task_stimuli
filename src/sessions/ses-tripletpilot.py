N_RUNS_PER_SESSION = 2
TRIPLET_DATA_PATH = "data/language/triplets/"

def get_tasks(parsed):
    from ..tasks import language, task_base
    TASKS = [
        language.Triplet(
            f"{TRIPLET_DATA_PATH}/designs/sub-{parsed.subject}_ses-pilot{parsed.session}_run-{run+1:02d}_design.tsv",
            name=f"task-triplets_run-{run+1:02d}",
            use_eyetracking=True,
        )
        for run in range(N_RUNS_PER_SESSION)
    ] + \
    [
        language.WordFeatures(
            f"{TRIPLET_DATA_PATH}/words_designs/sub-{parsed.subject}_ses-pilot{parsed.session}_run-{run+1:02d}_design.tsv",
            name="task-singlewords",
            use_eyetracking=True,
        )
        for run in range(N_RUNS_PER_SESSION)
    ]
    return TASKS
