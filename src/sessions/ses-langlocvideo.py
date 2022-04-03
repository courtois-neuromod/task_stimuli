from ..tasks import language

# set = 1 - 5, depending on i) whether the subject has been scanned on this task before,
# and ii) how many times they have been scanned (e.g. If a subject has been scanned
# twice, they should have seen sets 1 and then 2, so should be shown set 3 in their current
# session; NB: for first-time subjects, set should be 1 for both runs)
set_N  = 1 

#  One run is sufficient to localize the language regions in most participants, but we always
# recommend doing 2 runs, so as to be able to estimate the magnitudes of response using
# across-runs cross-validation

TASKS = []
for run_N in range(1, 2):
    TASKS.append(
        language.Reading(
            f"data/language/localizer/video/langloc_fmri_run{run_N}_stim_set{set_N}.tsv",
            name=f"langlocvideo_run{run_N}",
            cross_duration=2,
            txt_size=124,
        )
    )