import os

STIMULI_PATH = 'data/language/localizer'


ALICE_INSTRUCTIONS = """
Please listen attentively to the short passages from Alice in Wonderland in different languages (English/French/Tagalog) and to degraded versions of those passages.
"""

LISTENING_INSTRUCTIONS = """
Please listen attentively to the short passages in English and to degraded versions of those passages.
"""

READING_INSTRUCTIONS = """
Please read attentively the sentences or sequences of word-like nonwords.
The materials will be shown one word/nonword at a time.
"""

def get_tasks(parsed):
    import pandas as pd
    study_design = pd.read_csv(STIMULI_PATH + '/designs/all_localizers.tsv', sep='\t')

    session_design = study_design[
        study_design.subject_id.eq(int(parsed.subject)) &
        study_design.session.eq(int(parsed.session))
        ]

    print("#"*10 + " tasks for today "+"#"*10)
    for _, run in session_design.iterrows():
        print(f"- func_task-{run.task}")
    tasks = []
    from ..tasks import language, narratives, task_base
    first_task = True
    for _, run in session_design.iterrows():
        design_idx = int(run.design_file.split('_')[-1])
        if run.task == 'reading':
            tasks.append(
                language.ReadingBlocks(
                    os.path.join(
                        STIMULI_PATH,
                        f'designs/task-locreading_run-{design_idx:02d}_design.tsv'),
                    instruction=READING_INSTRUCTIONS,
                    use_eyetracking=True,
                    et_calibrate=True,
                    name='task-reading'
                )
            )
        elif run.task == 'listening':
            tasks.append(
                language.ListeningBlocks(
                    os.path.join(STIMULI_PATH, f'designs/listening_run{design_idx}.tsv'),
                    STIMULI_PATH,
                    instruction=LISTENING_INSTRUCTIONS,
                    use_eyetracking=True,
                    et_calibrate=first_task,
                    name='task-listening'
                )
            )
        elif 'alice' in run.task:
            tasks.append(
                language.ListeningBlocks(
                    os.path.join(STIMULI_PATH, f'designs/{run.task}_run{design_idx}.tsv'),
                    os.path.join(STIMULI_PATH, 'alice'),
                    instruction = ALICE_INSTRUCTIONS,
                    use_eyetracking=True,
                    et_calibrate=first_task,
                    name=f'task-{run.task}'
                )
            )
            first_task = False
    return tasks

INITIAL_WAIT = 6
FINAL_WAIT = 9
FIXATION_DURATION = 14
WORD_DURATION = .45
BUTTON_PRESS_DURATION=.5
SENTENCE_LEN = 12
TRIAL_ISI = .1
TRIAL_DURATION = TRIAL_ISI + WORD_DURATION * SENTENCE_LEN + BUTTON_PRESS_DURATION

import glob
import pandas as pd


def generate_reading_designs():

    reading_set_files = sorted(glob.glob(STIMULI_PATH + '/video/*.csv'))

    for rsfi, rsf in enumerate(reading_set_files):
        reading_set = pd.read_csv(rsf)
        design = pd.DataFrame(set_to_events(reading_set))
        out_fname = STIMULI_PATH + f"/designs/task-locreading_run-{rsfi+1:02d}_design.tsv"
        design.to_csv(out_fname, index=False, sep='\t')
        print(out_fname)


def set_to_events(reading_set):

    yield dict(trial_type='fix', onset=0, duration=FIXATION_DURATION)
    for rs_idx, rs in reading_set.iterrows():

        block = rs_idx // 3
        trial_onset = FIXATION_DURATION * (rs_idx//12+1) + rs_idx * TRIAL_DURATION
        yield dict(trial_type='fix', block=block, onset=trial_onset, duration=TRIAL_ISI)

        for word_idx in range(12):
            tt = 'word' if rs['stim14']=='S' else 'non-word'
            yield dict(trial_type=tt, word=rs[f"stim{word_idx+2}"], block=block, trial_idx=rs_idx, onset=trial_onset + TRIAL_ISI + word_idx * WORD_DURATION, duration=WORD_DURATION)

        yield dict(trial_type='press', block=block, trial_idx=rs_idx, onset=trial_onset + TRIAL_ISI + SENTENCE_LEN * WORD_DURATION, duration=BUTTON_PRESS_DURATION)

        if block % 4 == 3 and rs_idx % 12 == 11 :
            yield dict(trial_type='fix', onset=trial_onset  + TRIAL_ISI + SENTENCE_LEN * WORD_DURATION + BUTTON_PRESS_DURATION, duration=FIXATION_DURATION)



if __name__ == "__main__":
    generate_reading_designs()
