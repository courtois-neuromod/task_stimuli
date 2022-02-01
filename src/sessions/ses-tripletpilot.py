N_RUNS_PER_SESSION = 2

def get_tasks(parsed):
    from ..tasks import language, task_base
    TASKS = [
        language.Triplet(
            f"data/language/triplet/designs/sub-{parsed.subject}_ses-pilot{parsed.session}_run-{run+1:02d}_design.tsv", name="task-triplets"
        )
        for run in range(N_RUNS_PER_SESSION)
    ]
    return TASKS
