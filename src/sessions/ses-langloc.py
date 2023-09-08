import os
from ..tasks import language, task_base

STIMULI_PATH = 'data/language/localizer'

TASKS = [
    language.ReadingBlocks(
        os.path.join(STIMULI_PATH, 'video/langloc_fmri_run1_stim_set1.csv'),
        name='task-locreading_run-01'),
    language.ListeningBlocks(
        os.path.join(STIMULI_PATH, 'designs/auditory_1.tsv'),
        os.path.join(STIMULI_PATH, 'funloc_norm_clips'),
        name='task-locauditory_run-01')
]

INITIAL_WAIT = 6
FINAL_WAIT = 9
FIXATION_DURATION = 14
WORD_DURATION = .45
BUTTON_PRESS_DURATION=.5
SENTENCE_LEN = 12
TRIAL_ISI = .1
TRIAL_DURATION = TRIAL_ISI + WORD_DURATION * SENTENCE_LEN + BUTTON_PRESS_DURATION


def generate_reading_designs():
    import glob
    import pandas as pd

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
