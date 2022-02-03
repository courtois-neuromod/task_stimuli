
def get_tasks(parsed):
    from ..tasks import language, task_base
    TASKS = [
        language.WordFeatures(
            f"{TRIPLET_DATA_PATH}/words_designs/sub-{parsed.subject}_ses-{parsed.session}_run-{run+1:02d}_design.tsv",
            name="task-singlewords",
            use_eyetracking=True,
        )
        for run in range(N_RUNS_PER_SESSION)
    ]
    return TASKS


TRIPLET_DATA_PATH = "data/language/triplets/"
TR=1.49
N_BLOCKS_PER_RUN = 4
N_TRIALS_PER_BLOCK = 25
N_TRIALS_PER_RUN = N_BLOCKS_PER_RUN * N_TRIALS_PER_BLOCK
N_RUNS_PER_SESSION = 2
STIMULI_DURATION = .5
TRIAL_DURATION = 2*TR
BASELINE_BEGIN = 9
BASELINE_END = 9
ISI = TRIAL_DURATION - STIMULI_DURATION
ISI_JITTER = 0
FEATURES_INSTRUCTION_DURATION = 3*TR
POST_FEATURES_INSTRUCTION_ISI = 1*TR


SENSORIMOTOR_FEATURES = [
    "by feeling through touch",
    "by hearing",
    "by sensations inside your body",
    "by smelling",
    "by tasting",
    "by performing an action with your foot/leg",
    "by performing an action with your hand/arm",
    "by performing an action with your head",
    "by performing an action with your mouth/throat",
    "by performing an action with your torso",
]

def generate_design_file(subject, all_words, pilot=False):
    import os
    import hashlib
    import numpy as np

    # sample all ISI with same seed for matching run length
    np.random.seed(0)
    isi_set = np.random.random_sample(N_TRIALS_PER_RUN)*ISI_JITTER + ISI
    # seed numpy with subject id to have reproducible design generation
    seed = int(
        hashlib.sha1(("%s" % (subject)).encode("utf-8")).hexdigest(), 16
    ) % (2 ** 32 - 1)
    print("seed", seed)
    np.random.seed(seed)

    # randomize for participant
    all_words = all_words.sample(frac=1)


    for run in range(int(np.ceil(len(all_words)/N_TRIALS_PER_RUN))):
        run_sm_feats = np.random.permutation(SENSORIMOTOR_FEATURES)[:N_BLOCKS_PER_RUN]

        run_words = all_words[run*N_TRIALS_PER_RUN:(run+1)*N_TRIALS_PER_RUN]
        if 'triple_ids' in run_words:
            del run_words['triple_ids']
        run_words = run_words.reset_index(drop=True)
        run_words['trial_type'] = 'word'
        run_words['trial_index'] = np.arange(len(run_words))
        run_words['block_index'] = run_words['trial_index']//N_TRIALS_PER_BLOCK
        run_words['isi'] = np.random.permutation(isi_set)[:len(run_words)]
        run_words['sensorimotor_feature'] = run_sm_feats.repeat(N_TRIALS_PER_BLOCK)[:len(run_words)]
        run_words['onset'] = BASELINE_BEGIN + \
            run_words['trial_index']*STIMULI_DURATION + \
            np.cumsum(run_words['isi']) + \
            run_words['block_index'] * (FEATURES_INSTRUCTION_DURATION + POST_FEATURES_INSTRUCTION_ISI)
        run_words['duration'] = STIMULI_DURATION
        run_words = pandas.concat(
            sum([[pandas.DataFrame({
                    'trial_type': ['feature_question'],
                    'onset': [run_words.onset[block*N_TRIALS_PER_BLOCK] - (FEATURES_INSTRUCTION_DURATION + POST_FEATURES_INSTRUCTION_ISI)],
                    'duration': [FEATURES_INSTRUCTION_DURATION],
                    'sensorimotor_feature': [run_words.sensorimotor_feature[block*N_TRIALS_PER_BLOCK]],
                    'block_index': [block],
                    'isi': [POST_FEATURES_INSTRUCTION_ISI],
                    }),
                  run_words[block*N_TRIALS_PER_BLOCK:(block+1)*N_TRIALS_PER_BLOCK]] \
              for block in range(int(np.ceil(len(run_words)/25)))],[]))


        session = run // N_RUNS_PER_SESSION + 1
        run_in_session = run % N_RUNS_PER_SESSION + 1

        out_fname = os.path.join(
            TRIPLET_DATA_PATH,
            "words_designs",
            f"sub-{parsed.subject}_ses-{'pilot' if pilot else ''}{session:03d}_run-{run_in_session:02d}_design.tsv",
        )
        print(f"writing {out_fname}")
        run_words.to_csv(out_fname, sep="\t", index=False)

if __name__ == "__main__":
    import argparse
    import sys, os
    import pandas

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="generate design files for participant / session",
    )
    parser.add_argument("subject", type=str, help="participant id")
    parser.add_argument(
        "--pilot", help="Use pilot set", action="store_true"
    )

    parsed = parser.parse_args()
    if parsed.pilot:
        all_words = pandas.read_csv(os.path.join(TRIPLET_DATA_PATH, 'pilotable_words_v2.tsv'),sep='\t')
    else:
        all_words = pandas.read_csv(os.path.join(TRIPLET_DATA_PATH, 'fMRI_unique_words.tsv'), sep='\t')
    generate_design_file(parsed.subject, all_words, parsed.pilot)
