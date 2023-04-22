import os
import re
import pandas as pd
import hashlib
import numpy as np
from itertools import product
from scipy.ndimage import label, generate_binary_structure


N_DESIGN_REPETITION = 5
N_GRID_PER_RUN = 4

def get_tasks(parsed):
    from ..tasks import memory
    tasks = []
    design_filename = os.path.join(
            NUMBER_PAIRS_DATA_PATH,
            "designs",
            f"sub-{parsed.subject}_design.tsv",
        )
    design = pd.read_csv(design_filename, sep='\t')
    total_n = design.shape[0]
    n_runs = int(total_n / N_GRID_PER_RUN)
    for run in range(n_runs):
        start = N_GRID_PER_RUN * run
        end = N_GRID_PER_RUN * (run + 1)
        total_possible_points = design.loc[start:end, ['target_score', 'reward_level']].values.sum()
        session_design_filename = os.path.join(
            NUMBER_PAIRS_DATA_PATH,
            "designs",
            f"sub-{parsed.subject}_task-numberpair_run-{run + 1}_events.tsv",
        )
        tasks.append(memory.NumberPair(name="task-numberpair_run-{run + 1}",
                                       items_list=session_design_filename,
                                       total_possible_points=total_possible_points))
    return tasks

# Task Parameters
# fMRI: runs of 10 minutes - 2 run max
# 10 minutes = 6 ~ 10 memory grids, 2 levels of
NUMBER_PAIRS_DATA_PATH = os.path.join("data", "memory", "numberpairs")
DIFFICULTY_SCALE = {  # The homogenous grid difficulty per target score level
    3: 0,
    4: 0,
    5: 0.4,
    6: 0.5,
    7: 0.8571,
    8: 1,
}

ALLOWED_ALPHABETS = "ABCDEFGHJKLMNPQRSTUVWXYZ"  # remove O and I

encoding_duration = 5  # lower limit per grid
recall_duration = 3  # upper limit per pair
feedback_duration = 3
estimate_duration = 8
# what are the reward levels?
REWARD_LEVEL = [1, 100]
# target score: number of pairs in the memeory grid
# what are the target scores to be tested?
TARGET_SCORE_LEVEL = [4, 8]
GRID_SIZE = (4, 6)

# how many repetitions of each (target scores x reward level) condition?
# (should be even if using contiguous task conditions)
# len(REWARD_LEVEL) * len(TARGET_SCORE_LEVEL) * N_META_BLOCK == number of total trials
# how many different grid/task condition sets to generate?
N_SUBJECTS = 1

N_PERMUTATION = 1000  # how many permutations to check?

# fMRI parameters
TR = 1.49  # this has to be double checked
ISI = 3  # 3 seconds jittered
ISI_JITTER = 2


def generate_design_file(target_score_level, reward_level, n_design_repetition, seed):
    """Generate memory grids based on the target score and reward leve."""
    # seed numpy with subject id and session to have reproducible design generation
    np.random.seed(seed)

    # number of memeory grid to generate
    n_reward = len(reward_level)
    n_target_score = len(target_score_level)
    n_condition = n_reward * n_target_score  # how many different conditions?
    n_trials_per_run = n_condition * n_condition * n_design_repetition

    # generate condion list
    n_samples = 10000
    n_max_condition_difference = 0

    def generate_best_condition(n_memory_grid, n_condition, n_samples, contiguous=True):
        """
        Generates a vector of blocks (n_blocks = n_memory_grid/n_condition) of task
        condition levels where the difference in trial

        if contiguous, each block contains two of each task condition in a sequential order.
        Example: 2x2 design of two blocks: [1 1 2 2 3 3 4 4 2 2 1 1 4 4 3 3]

        if contiguous, n_memory_grid/2 must be divisible by n_condition.
        else: n_memory_grid must be divisible by n_condition

        !! Will only work for a balanced design !!

        Parameters:
            n_memory_grid (int): number of trials.
            n_condition (int): number of conditions.
            n_samples (int): number of samples to take for permutations.

        Returns:
            conditions (numpy.ndarray): array of condition permutations where the
            difference in trial index between repeats of each condition is maximised.
            max_condition_distance: maximum distance of conditions.
        """
        if contiguous:
            n_memory_grid = int(n_memory_grid / 2)

        conditions = []
        min_condition_distances = []
        for _ in range(n_samples):
            tmp_conditions = _generate_conditions(n_memory_grid, n_condition)
            conditions.append(tmp_conditions)
            min_condition_distances.append(
                _get_condition_distance(tmp_conditions, n_condition)
            )

        max_condition_distance = np.max(min_condition_distances)
        ind = np.array(min_condition_distances) == max_condition_distance
        conditions = np.array(conditions)[ind]
        if contiguous:
            conditions = np.repeat(conditions, 2, axis=1)

        # make sure each row is unique
        return np.unique(conditions, axis=0), max_condition_distance

    def _generate_conditions(n_memory_grids, n_condition):
        """Randomly generate condition for each memory grid."""
        if n_memory_grids % n_condition != 0:
            raise ValueError(
                "n_memory_grid must be divisible by n_condition. Current values "
                f"n_memory_grid: {n_memory_grids}\nn_condition: {n_condition}."
            )
        n_blocks = n_memory_grids // n_condition
        condition_perm = np.empty((n_blocks, n_condition), dtype=int)

        # permute within block
        for i in range(n_blocks):
            condition_perm[i, :] = np.random.permutation(np.arange(n_condition)) + 1
        return condition_perm.ravel()

    def _get_condition_distance(conditions, n_condition):
        # get the minimal distance of each condition in a list of task conditions
        minimal_distance = []
        for i in range(n_condition):
            idx_current_condition = np.where(conditions == i + 1)[0]
            minimal = np.min(np.diff(idx_current_condition))
            minimal_distance.append(minimal)  # minimum distance for this condition
        return np.min(minimal_distance)  # minimum distance of any condition

    def homogenise_grid_difficulty(
        grid_size, target_score_array, reward_array, target_score_levels
    ):
        """Generates a set of permutations of pairs on an n_row x n_col grid
        with difficulty = target_difficulty.
        The same set of grids is generated for each participant and organised
        according to their individual sequence of
        target scores. The higher the score, the easier the grid.
        """
        designs = []
        for s in range(target_score_array.shape[0]):
            n_needed_pairs_per_level = [
                np.sum(target_score_array[0, :] == x) for x in target_score_levels
            ]
            # Loop through target score levels and generate enough valid trials
            valid_memory_grids = {}
            for n_pairs, needed_pairs in zip(
                target_score_levels, n_needed_pairs_per_level
            ):
                # Generate all grids for nTSLvl
                current_grid_location = []
                current_grid_difficulty = []
                valid_memory_grids[n_pairs] = []
                while len(current_grid_location) < needed_pairs:
                    grid, difficulty_score = find_valid_grid(grid_size, n_pairs)
                    # if grid already exist, disgard and find the next one
                    if any(np.array_equal(c, grid) for c in current_grid_location):
                        continue
                    current_grid_location.append(grid)
                    current_grid_difficulty.append(difficulty_score)
                for l, d in zip(current_grid_location, current_grid_difficulty):
                    valid_memory_grids[n_pairs].append((l, d))

            sdf = pd.DataFrame()
            for ts_level in target_score_array[s, :]:
                grid, difficulty = valid_memory_grids[ts_level].pop()
                grid = _make_memory_grid(grid, grid_size)
                df = {
                    "grid": [grid],
                    "difficulty": [np.mean(difficulty)],
                    "target_score": [ts_level],
                }
                df = pd.DataFrame(df)
                sdf = pd.concat([sdf, df])
            sdf = sdf.reset_index(drop=True)
            sdf["reward_level"] = reward_array[s, :]
            # assign metablock (minimal block size for a run?)
            designs.append(sdf)
        return designs

    def _make_memory_grid(grid, grid_size):
        """Fill the memory grid with filler alphabets."""
        n_space = grid_size[0] * grid_size[1]

        fillers = np.random.choice(len(ALLOWED_ALPHABETS), size=n_space, replace=False)

        return "".join(
            str(c) if c > 0 else list(ALLOWED_ALPHABETS)[fillers[i]]
            for i, c in enumerate(grid.flatten().tolist())
        )

    def find_valid_grid(
        grid_size, n_pairs, grid=None, difficulty_score_per_pair=(10, 10), verbose=0
    ):
        """
        Find valid grid that fits the difficulty level.
        """
        threshold = DIFFICULTY_SCALE[n_pairs]
        grid_difficulty_score = np.mean(difficulty_score_per_pair)
        if (
            np.absolute(grid_difficulty_score - threshold) < 0.0001
            and np.sum(difficulty_score_per_pair == 2) < 3
        ):
            if verbose != 0:
                print(
                    f"Found grid containing {n_pairs} pairs of targets, at score {threshold}"
                )
                print(grid, np.mean(difficulty_score_per_pair))
            return grid, difficulty_score_per_pair
        # get a grid
        grid = _generate_number_pairs_grids(grid_size, n_pairs)
        # homogenous score
        difficulty_score_per_pair = _calculate_homogenous_score(grid)
        return find_valid_grid(grid_size, n_pairs, grid, difficulty_score_per_pair)

    def _calculate_homogenous_score(grid):
        n_pairs = np.max(grid)
        difficulty_score_per_pair = np.zeros(n_pairs)
        for x in range(1, n_pairs + 1):
            # Calculate contiguous pairs
            s = generate_binary_structure(2, 2)
            contiguous = int(label(grid == x, structure=s)[-1] == 1)
            # Calculate aligned pairs
            aligned = _check_alignment(grid, x)
            difficulty_score_per_pair[x - 1] += contiguous + aligned
        return difficulty_score_per_pair

    def _check_alignment(tmp_grid, x):
        verticle_aligned = np.sum(tmp_grid == x, axis=0)
        verticle_aligned = np.where(verticle_aligned == 2)[0].size > 0
        horisontal_aligned = np.sum(tmp_grid == x, axis=1)
        horisontal_aligned = np.where(horisontal_aligned == 2)[0].size > 0
        return any([verticle_aligned, horisontal_aligned])

    def _generate_number_pairs_grids(grid_size, n_pairs):
        memory_grid = np.zeros(grid_size, dtype=int)
        idx_number_pairs = np.random.choice(
            grid_size[0] * grid_size[1], size=n_pairs * 2, replace=False
        )
        idx_number_pairs = idx_number_pairs.tolist()
        memory_grid.flat[idx_number_pairs] = np.repeat(range(1, n_pairs + 1), 2)
        return memory_grid

    while n_max_condition_difference < N_SUBJECTS:
        max_difference_conditions, max_difference = generate_best_condition(
            n_trials_per_run, n_condition, n_samples, contiguous=True
        )
        if (
            len(np.unique(max_difference_conditions, axis=0))
            != max_difference_conditions.shape[0]
        ):  # check no condition repeats
            continue
        n_max_condition_difference = max_difference_conditions.shape[0]
        n_samples = int(
            n_samples * 1.3
        )  # if we didn't find enough condition permutations, permute more!

    # take the first N_SUBJECTS as the list for the experiment.
    memory_grids_conditions = max_difference_conditions[:N_SUBJECTS, :]

    # translate the condition back to reward and target score
    # generate all combination of reward and target score
    reward_translator, target_score_translator = {}, {}
    for i, (t, r) in enumerate(product(target_score_level, reward_level), 1):
        reward_translator[i] = r
        target_score_translator[i] = t

    reward_array = (
        pd.DataFrame(memory_grids_conditions.copy()).replace(reward_translator).values
    )  # reward level for each subject
    target_score_array = (
        pd.DataFrame(memory_grids_conditions.copy())
        .replace(target_score_translator)
        .values
    )  # target score for each subject

    # Homogenise grid difficulty
    designs = homogenise_grid_difficulty(
        GRID_SIZE, target_score_array, reward_array, target_score_level
    )
    designs =  designs[0]  # original code was for generating multiple designs
    return designs


def create_event_file(designs, seed):
    """Take the design and flash out the event that will be desplayed."""
    # sample all ISI with same seed for matching run length
    np.random.seed(0)
    n_trials= designs.shape[0]
    n_isi_needed = 1000  # just generate a bunch
    isi_set = (
        np.random.random_sample(n_isi_needed) * ISI_JITTER
        - ISI_JITTER / 2
        + ISI
    )
    isi_set = isi_set.round(2).tolist()
    print(f"{n_trials} events")
    np.random.seed(seed)

    def _generate_recall_grid(i, row):
        """Break down the encoding grid into recall events."""
        numbers = list(range(1, row["target_score"] + 1))
        _ = numbers.pop(i)  # remove the current number testing
        numbers = "".join([str(n) for n in numbers])
        pattern = f"[A-Z{numbers}]"
        # find the location index of the current number
        recall_grid = re.sub(pattern, r" ", row["grid"])
        current_number_loc = np.array(
            [loc for loc, c in enumerate(recall_grid) if c.isdigit()]
            )
        np.random.shuffle(current_number_loc)
        # the first one will be the answer
        recall_answer = current_number_loc[0]
        # remove the answer from the grid, replace with empty space
        recall_grid = (f"{recall_grid[:recall_answer]} "
                       f"{recall_grid[recall_answer + 1:]}")
        return recall_grid,current_number_loc,recall_answer


    def _switch_condition(designs, trial, row):
        """Check if the target score x reward level pair changes next."""
        if trial == designs.shape[0] - 1:
            return True
        next_ts = designs.loc[trial + 1, "target_score"]
        next_rl = designs.loc[trial + 1, "reward_level"]
        return (next_rl != row["reward_level"]) or (next_ts != row["target_score"])

    event_file = pd.DataFrame()
    for i_encoding, row in designs.iterrows():
        recalls = {
            "duration": [estimate_duration],
            "event_type": ["estimate"],
            "pair_number": ["--"],
            "grid": ["select encoding time"],
            "recall_display": ["--"],
            "recall_answer": ["--"],
        }
        recalls["duration"].append(isi_set.pop())
        recalls["event_type"].append("isi")
        recalls["pair_number"].append("--")
        recalls["recall_display"].append("--")
        recalls["recall_answer"].append("--")
        recalls["grid"].append("")

        recalls["duration"].append(encoding_duration)
        recalls["event_type"].append("encoding")
        recalls["pair_number"].append("--")
        recalls["recall_display"].append("--")
        recalls["recall_answer"].append("--")
        recalls["grid"].append(row["grid"])

        recalls["duration"].append(isi_set.pop())
        recalls["event_type"].append("isi")
        recalls["pair_number"].append("--")
        recalls["recall_display"].append("--")
        recalls["recall_answer"].append("--")
        recalls["grid"].append("")

        for i in range(row["target_score"]):
            recall_grid, current_number_loc, recall_answer = _generate_recall_grid(i, row)
            # the last one will be the displayed
            recalls["duration"].append(recall_duration)
            recalls["event_type"].append("recall")
            recalls["pair_number"].append(i + 1)
            recalls["recall_display"].append(current_number_loc[-1])
            recalls["recall_answer"].append(recall_answer)
            recalls["grid"].append(recall_grid)

        recalls["duration"].append(isi_set.pop())
        recalls["event_type"].append("isi")
        recalls["pair_number"].append("--")
        recalls["recall_display"].append("--")
        recalls["recall_answer"].append("--")
        recalls["grid"].append("--")

        recalls["duration"].append(estimate_duration)
        recalls["event_type"].append("e_success")
        recalls["pair_number"].append("--")
        recalls["recall_display"].append("--")
        recalls["recall_answer"].append("--")
        recalls["grid"].append("how many did you get right")

        recalls["duration"].append(isi_set.pop())
        recalls["event_type"].append("isi")
        recalls["pair_number"].append("--")
        recalls["recall_display"].append("--")
        recalls["recall_answer"].append("--")
        recalls["grid"].append("--")

        if _switch_condition(designs, i_encoding, row):
            recalls["duration"].append(estimate_duration)
            recalls["event_type"].append("effort")
            recalls["recall_display"].append("--")
            recalls["recall_answer"].append("--")
            recalls["grid"].append("how much effort")
            recalls["pair_number"].append("--")

            recalls["duration"].append(isi_set.pop())
            recalls["event_type"].append("isi")
            recalls["recall_display"].append("--")
            recalls["recall_answer"].append("--")
            recalls["grid"].append("--")
            recalls["pair_number"].append("--")

        recalls["duration"].append(feedback_duration)
        recalls["event_type"].append("feedback")
        recalls["recall_display"].append("--")
        recalls["recall_answer"].append("--")
        recalls["grid"].append("feed back screen")
        recalls["pair_number"].append(-1)

        recalls["duration"].append(TR * 2)  # block end
        recalls["event_type"].append("isi")
        recalls["recall_display"].append("--")
        recalls["recall_answer"].append("--")
        recalls["grid"].append("--")
        recalls["pair_number"].append("--")

        recalls = pd.DataFrame(recalls)
        recalls["i_grid"] = i_encoding + 1
        recalls["difficulty"] = row["difficulty"]
        recalls["target_score"] = row["target_score"]
        recalls["reward_level"] = row["reward_level"]
        recalls.index.name = "event_index"
        event_file = pd.concat((event_file, recalls))
    return event_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="generate design files for participant.",
    )
    parser.add_argument("subject", type=str, help="participant id")
    parser.add_argument(
        "--target_score_level",
        nargs="+",
        type=int,
        default=TARGET_SCORE_LEVEL,
        help="A list of target score range from 3 to 8.",
    )
    parser.add_argument(
        "--reward_level",
        nargs="+",
        type=int,
        default=REWARD_LEVEL,
        help="A list of reward level.",
    )

    parsed = parser.parse_args()

    # generate seed
    seed = int(hashlib.sha1(f"{parsed.subject}".encode("utf-8")).hexdigest(), 16) % (2**32 - 1)
    print("seed for design", seed)
    n_condition = len(parsed.reward_level) * len(parsed.target_score_level)

    # n_condition * n_condition is the minimum amount of memeory blocks for one valid design
    n_trials = n_condition * n_condition * N_DESIGN_REPETITION
    # design
    designs = generate_design_file(parsed.target_score_level,
                                   parsed.reward_level,
                                   N_DESIGN_REPETITION,
                                   seed)
    # save for review
    out_fname = os.path.join(
        NUMBER_PAIRS_DATA_PATH,
        "designs",
        f"sub-{parsed.subject}_design.tsv",
    )
    designs.to_csv(out_fname, sep="\t", index=True)

    # event
    total_n = designs.shape[0]
    n_runs = int(total_n / N_GRID_PER_RUN)
    for i in range(n_runs):
        seed = int(hashlib.sha1(f"{parsed.subject}_{1+i}".encode("utf-8")).hexdigest(), 16) % (2**32 - 1)
        print(f"seed for design run {1 + i}", seed)
        start = N_GRID_PER_RUN * i
        end = N_GRID_PER_RUN * (i + 1)
        current_design = designs.iloc[start: end, :].reset_index()
        event_file = create_event_file(current_design, seed)
        out_fname = os.path.join(
            NUMBER_PAIRS_DATA_PATH,
            "designs",
            f"sub-{parsed.subject}_task-numberpair_run-{i+1}_events.tsv",
        )
        event_file = event_file.reset_index()
        event_file.to_csv(out_fname, sep="\t", index=True)
