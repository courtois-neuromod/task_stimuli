from ..tasks import language, task_base

TASKS = [
    language.Triplet(
        "data/language/triplet/test_triplets.tsv", name="task-triplets"
    ),
    task_base.Pause(text="Take a break. Press any key to continue...", wait_key=None),
]
