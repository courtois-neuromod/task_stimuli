
TRIPLET_DATA_PATH = "data/language/triplet/"
TR=1.49
N_BLOCKS_PER_RUN = 4
N_TRIALS_PER_BLOCK = 25
N_TRIALS_PER_RUN = N_BLOCKS_PER_RUN * N_TRIALS_PER_BLOCK
N_RUNS_PER_SESSION = 2
STIMULI_DURATION = .5
TRIAL_DURATION = 2*TR
BASELINE_BEGIN = 6
BASELINE_END = 9
ISI = TRIAL_DURATION - STIMULI_DURATION
ISI_JITTER = 0
FEATURES_INSTRUCTION_DURATION = 2*TR

def generate_design_file(subject, all_words, pilot=False):
    import os
    import hashlib
    import numpy as np
    from src.tasks.language import WordFeatures

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



    for run in range(int(np.ceil(len(all_triplets)/N_TRIALS_PER_RUN))):
        run_sm_feats = np.random.permutation(WordFeatures.SENSORIMOTOR_FEATURES)[:N_BLOCKS_PER_RUN]

        run_words = run_words[run*N_TRIALS_PER_RUN:(run+1)*N_TRIALS_PER_RUN]
        run_words['trial_index'] = np.arange(len(run_words))
        run_words['block_index'] = run_words['trial_index']//N_BLOCKS_PER_RUN
        run_words['isi'] = np.random.permutation(isi_set)[:len(run_words)]
        run_words['sensorimotor feature'] = run_sm_feats.repeat(N_TRIALS_PER_BLOCK)
        run_words['onset'] = BASELINE_BEGIN + \
            run_words['trial_index']*STIMULI_DURATION + \
            np.cumsum(run_words['isi']) + \
            run_words['block_index'] * FEATURES_INSTRUCTION_DURATION
        run_words['duration'] = STIMULI_DURATION



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
        all_words = pandas.read_csv(os.path.join(TRIPLET_DATA_PATH, 'pilotable_words_v2.csv'))
    else:
        all_words = pandas.read_csv(os.path.join(TRIPLET_DATA_PATH, 'fMRI_unique_words.csv'))
    generate_design_file(parsed.subject, all_words, parsed.pilot)
