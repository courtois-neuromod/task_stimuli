from ..tasks import language

TASKS = []
for seg_idx in range(1, 8):
    TASKS.append(
        language.Reading(
            "data/language/harrypotter/task-harry_run-%d_events.tsv" % seg_idx,
            name="harrypotter_seg-%d" % seg_idx,
        )
    )

