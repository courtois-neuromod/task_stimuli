from ..tasks import language

TASKS = []
for run in range(1, 8):
    TASKS.append(
        language.Reading(
            f"data/language/harrypotter/task-harry_run-{run}_events.tsv",
            name=f"harrypotter_run-{run}",
            cross_duration=2,
            txt_size=124,
        )
    )