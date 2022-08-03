from ..tasks import language, task_base

TASKS = [
    language.Triplet(
        "data/language/triplet/first1000triples.csv", wait_key=True, name="triplet_test"
    ),
    task_base.Pause(text="Take a break. Press any key to continue...", wait_key=None),
    language.Triplet(
        "data/language/triplet/first1000triples.csv", wait_key=True, name="triplet_test"
    ),
    task_base.Pause(text="Take a break. Press <a> to continue...", wait_key=["a"]),
]
