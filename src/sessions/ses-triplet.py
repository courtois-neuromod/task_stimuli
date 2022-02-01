def get_tasks(parsed):
    from ..tasks import language, task_base
    TASKS = [
        language.Triplet(
            f"data/language/triplet/designs/sub-{parsed.subject}_ses-{parsed.session}_run-{run+1:02d}_design.tsv", name="task-triplets"
        )
        for run in range(N_RUNS_PER_SESSION)
    ]
    return TASKS

TRIPLET_DATA_PATH = "data/language/triplet/"
TR=1.49
N_TRIALS_PER_RUN = 100
N_RUNS_PER_SESSION = 2
STIMULI_DURATION = 4
TRIAL_DURATION = 4*TR
BASELINE_BEGIN = 6
BASELINE_END = 9
ISI = TRIAL_DURATION - STIMULI_DURATION
ISI_JITTER = 0

def generate_design_file(subject, all_triplets, pilot=False):
    import os
    import hashlib
    import numpy as np

    # seed numpy with subject id to have reproducible design generation
    seed = int(
        hashlib.sha1(("%s" % (subject)).encode("utf-8")).hexdigest(), 16
    ) % (2 ** 32 - 1)
    print("seed", seed)
    np.random.seed(seed)

    all_run_trials = pandas.DataFrame()
    print(all_triplets.shape)

    isi_set = np.random.random_sample(N_TRIALS_PER_RUN)*ISI_JITTER + ISI
    # permute categories per participant

    all_triplets = all_triplets.sample(frac=1)
    for run in range(int(np.ceil(len(all_triplets)/N_TRIALS_PER_RUN))):
        run_triplets = all_triplets[run*N_TRIALS_PER_RUN:(run+1)*N_TRIALS_PER_RUN]
        run_triplets['isi'] = np.random.permutation(isi_set)[:len(run_triplets)]
        run_triplets['onset'] = BASELINE_BEGIN + np.arange(len(run_triplets))*STIMULI_DURATION + np.cumsum(run_triplets['isi'])
        run_triplets['duration'] = STIMULI_DURATION

        session = run // N_RUNS_PER_SESSION + 1
        run_in_session = run % N_RUNS_PER_SESSION + 1

        out_fname = os.path.join(
            TRIPLET_DATA_PATH,
            "designs",
            f"sub-{parsed.subject}_ses-{'pilot' if pilot else ''}{session:03d}_run-{run_in_session:02d}_design.tsv",
        )
        print(f"writing {out_fname}")
        run_triplets.to_csv(out_fname, sep="\t", index=False)

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
        all_triplets = pandas.read_csv(os.path.join(TRIPLET_DATA_PATH, 'pilotable_triplets_v2.csv'), index_col=0)
        all_triplets = pandas.DataFrame({
            'target': all_triplets.target,
            'choice_1': all_triplets.candidate_1,
            'choice_2': all_triplets.candidate_2,
        })
    else:
        all_triplets = pandas.read_csv(os.path.join(TRIPLET_DATA_PATH, 'fMRI_triplets.csv'), index_col=0)
    generate_design_file(parsed.subject, all_triplets, parsed.pilot)
