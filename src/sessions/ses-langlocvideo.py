from ..tasks import language

run_N = 1 

TASKS = []
for set_N in range(1, 5):
    TASKS.append(
        language.Reading(
            f"data/language/localizer/video/langloc_fmri_run{run_N}_stim_set{set_N}.tsv",
            name=f"langlocvideo_run{run_N}",
            cross_duration=2,
            txt_size=124,
        )
    )