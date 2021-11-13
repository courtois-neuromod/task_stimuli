import os

PURE_TONES_DATA_PATH = os.path.join("data", "audio")
SOUND_PATH = os.path.join(PURE_TONES_DATA_PATH, "pure_tones")


def get_tasks(parsed):
    from ..tasks.pure_tones import PureTones

    session_design_filename = os.path.join(
        PURE_TONES_DATA_PATH,
        "intensity_designs",
        f"sub-{parsed.subject}_ses-{parsed.session}_design.tsv",
    )
    n_runs_session = n_runs if int(parsed.session) > 1 else n_runs//2
    tasks = [
        PureTones(
            session_design_filename,
            SOUND_PATH,
            run,
            name=f"task-puretones_run-{run}",
            use_eyetracking=False,
            use_fmri=parsed.fmri,
            use_meg=parsed.meg,
            )
        for run in range(1, n_runs_session + 1)
    ]
    return tasks

get_tasks(tasks="pure_tones", session="test001")
