from ..tasks import language

TASKS = []
for seg_idx in range(1, 2):
    TASKS.append(
        language.Reading(
            "data/language/triplet/first1000triples.csv",
            name="harrypotter_seg-%d" % seg_idx,
            cross_duration=2,
            txt_size=124,
        )
    )

# ??? volumes each, last run is ??? volumes long
