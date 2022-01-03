import os

PURE_TONES_DATA_PATH = os.path.join("data", "audio")
SOUND_PATH = os.path.join(PURE_TONES_DATA_PATH, "stimuli")


def get_tasks(parsed):
    from ..tasks.pure_tones import PureTones
    
    n_runs = 1
    
    sub_number = ""
    for i in range(0, len(parsed.subject)):
        if parsed.subject[i].isdigit():
            sub_number += str(parsed.subject[i])
        else:
            continue

    session_design_filename = os.path.join(
        PURE_TONES_DATA_PATH,
        "auditory_designs",
        f"sub-{sub_number}_ses-{parsed.session}_task-puretones_events.tsv",
    )

    n_runs_session = n_runs if int(parsed.session) > 1 else n_runs//2

    tasks = PureTones(sub=parsed.subject,
                      design=session_design_filename,
                      ISI=5)

    tasks._run(run_number=parsed.session)
    return tasks


#get_tasks({"--subjects": "test", "--session": "test001", "--tasks": "pure_tones", "-o": "../../data/audio/pure_tones"})
