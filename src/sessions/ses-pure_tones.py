import os

PURE_TONES_DATA_PATH = os.path.join("data", "audio")
SOUND_PATH = os.path.join(PURE_TONES_DATA_PATH, "stimuli")


def get_tasks(parsed):
    from ..tasks.pure_tones import PureTones

    n_runs = 1

    session_design_filename = os.path.join(
        PURE_TONES_DATA_PATH,
        "auditory_designs",
        f"sub-{parsed.subject}_ses-{parsed.session}_task-puretones_events.tsv",
    )

    n_runs_session = n_runs if int(parsed.session) > 1 else n_runs//2

    tasks = [PureTones(sub=parsed.subject,
                      design=session_design_filename,
                      ISI=5,
                      name='task-puretones')]

    return tasks


#get_tasks({"--subjects": "test", "--session": "test001", "--tasks": "pure_tones", "-o": "../../data/audio/pure_tones"})
