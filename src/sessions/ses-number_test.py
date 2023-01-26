import os, re

NUMBER_PAIRS_DATA_PATH = os.path.join("data", "memory", "number_pairs")


def get_tasks(parsed):
    from ..tasks import memory

    session_design_filename = os.path.join(
        NUMBER_PAIRS_DATA_PATH,
        "designs",
        f"sub-{parsed.subject}_design.tsv",
    )
    tasks = [
        memory.NumberPair(
            name="numberpairs",
            items_list=session_design_filename
            )
    ]
    return tasks


# experiment

allowed_aphabets = "ABCDEFGHJKLMNPQRSTUVWXYZ"  # remove O and I
n_trials = 2
n_pairs = 4
trial_duration = 10
fixation_duration = 1

def generate_memory_items(grid_size=(5, 4), n_pairs=4):
    # for now just generate 20 characters mixed with numbers and alphabets
    import random
    items = [str(i + 1) for i in range(n_pairs)] * 2
    n_space = grid_size[0] * grid_size[1] - len(items)
    items += random.sample(list(allowed_aphabets), k=n_space)
    random.shuffle(items)
    return "".join(items)


def generate_isi(lb=0.50, ub=2.00):
    """Generate ISI given a uniform distribution, in seconds."""
    import numpy as np
    return np.round(np.random.uniform(lb, ub), 2)


def generate_design_file(subject):
    import pandas as pd
    import numpy as np
    import random

    trials = pd.DataFrame()

    for i in range(n_trials):
        if i == 0:
            # initalise a block with question to select the rehersal time
            onset_trial = 0
            grid = ["".join([" "] * 20)]
            onset = [onset_trial]
            duration = [generate_isi() + fixation_duration]
            recall_display = ["N/A"]
            recall_ans = ["N/A"]
            trial_type = ["fixation"]
            trial_number = [0]
            pair_number = [-1]
        else:
            onset_trial = block['onset'].values[-1] + block['duration'].values[-1]
            grid, onset, duration, recall_display, recall_ans, trial_type, trial_number, pair_number = [], [], [], [], [], [], [], []
        # initialise a block
        block = pd.DataFrame()
        # rehersal
        memory_grid = generate_memory_items()
        grid.append(memory_grid)  # generate rehersal trials
        onset.append(onset_trial)
        duration.append(trial_duration)
        recall_display.append("N/A")
        recall_ans.append("N/A")
        trial_type.append("rehersal")
        trial_number.append(i + 1)
        pair_number.append(0)

        # recall
        for j in range(n_pairs):
            # fixation
            grid.append("".join([" "] * 20))
            onset.append(onset[-1] + duration[-1])
            duration.append((generate_isi() + fixation_duration))
            recall_display.append("N/A")
            recall_ans.append("N/A")
            trial_type.append("fixation")
            trial_number.append(i + 1)
            pair_number.append(0)

            # response grid
            numbers = list(range(1, n_pairs + 1))
            current = numbers.pop(j)  # remove the current number testing
            numbers = "".join([str(n) for n in numbers])
            pattern = f"[A-Z{numbers}]"
            mem_grid = memory_grid
            # find the location index of the current number
            mem_grid = re.sub(pattern, r' ', mem_grid)
            current_number_loc = [loc for loc, c in enumerate(mem_grid) if c.isdigit()]
            random.shuffle(current_number_loc)  # shuffle
            current_ans_loc = current_number_loc[0] # the first one will be the answer
            current_display_loc = current_number_loc[-1] # the last one will be the displayed
            mem_grid = f"{mem_grid[:current_ans_loc]} {mem_grid[current_ans_loc + 1:]}"  # remove the answer
            grid.append(mem_grid)
            onset.append(onset[-1] + duration[-1] )
            duration.append(trial_duration)
            recall_display.append(current_display_loc)
            recall_ans.append(current_ans_loc)
            trial_type.append("recall")
            trial_number.append(i + 1)
            pair_number.append(j + 1)

        # fixation
        grid.append("".join([" "] * 20))
        onset.append(onset[-1] + duration[-1])
        duration.append((generate_isi() + fixation_duration))
        recall_display.append("N/A")
        recall_ans.append("N/A")
        trial_type.append("fixation")
        trial_number.append(0)
        pair_number.append(-1)

        block['trial_number'] = trial_number
        block['pair_number'] = pair_number
        block['grid'] = grid
        block['duration'] = duration
        block['onset'] = onset
        block['recall_display'] = recall_display
        block['recall_answer'] = recall_ans
        block['trial_type'] =trial_type

        trials = pd.concat((trials, block))
    # generate recall trials
    trials = trials.reset_index(drop=True)

    out_fname = os.path.join(
        NUMBER_PAIRS_DATA_PATH,
        "designs",
        f"sub-{subject}_design.tsv",
    )
    trials.to_csv(out_fname, sep="\t", index=True, index_label="index")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="generate design files for participant / session",
    )
    parser.add_argument("subject", type=str, help="participant id")
    parsed = parser.parse_args()
    generate_design_file(parsed.subject)
