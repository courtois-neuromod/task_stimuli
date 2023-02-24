from itertools import product
import numpy as np
import pandas as pd
from .numerpair_utils import generate_best_condition, homogenise_grid_difficulty


# Task Parameters


# what are the reward levels?
REWARD_LEVEL = [1, 2]
# target score: number of pairs in the memeory grid
# what are the target scores to be tested?
TARGET_SCORE_LEVEL = [3, 5, 7]
GRID_SIZE = (4, 6)

# how many repetitions of each (target scores x reward level) condition?
# (should be even if using contiguous task conditions)
N_META_BLOCK = 6
# how many different grid/task condition sets to generate?
N_SUBJECTS = 6

N_PERMUTATION = 1000    # how many permutations to check?

# number of memeory grid to generate
n_memory_grid = N_META_BLOCK * len(REWARD_LEVEL) * len(TARGET_SCORE_LEVEL)
n_cells = GRID_SIZE[0] * GRID_SIZE[1]
n_reward = len(REWARD_LEVEL)
n_target_score = len(TARGET_SCORE_LEVEL)
n_condition = n_reward * n_target_score    # how many different conditions?

# generate condion list
n_samples = 10000
n_max_condition_difference = 0
while n_max_condition_difference < N_SUBJECTS:
    max_difference_conditions, max_difference = generate_best_condition(n_memory_grid, n_condition, n_samples, contiguous=True)
    if len(np.unique(max_difference_conditions, axis=0)) != max_difference_conditions.shape[0]:    # check no condition repeats
        continue
    n_max_condition_difference = max_difference_conditions.shape[0]
    n_samples = int(n_samples * 1.3)    # if we didn't find enough condition permutations, permute more!

# take the first N_SUBJECTS as the list for the experiment
memory_grids_conditions = max_difference_conditions[:N_SUBJECTS, :]

# translate the condition back to reward and target score
# generate all combination of reward and target score
reward_translator, target_score_translator = {}, {}
for i, (t, r) in enumerate(product(TARGET_SCORE_LEVEL, REWARD_LEVEL), 1):
    reward_translator[i] = r
    target_score_translator[i] = t

reward_array = pd.DataFrame(memory_grids_conditions.copy()).replace(reward_translator).values  # reward level for each subject
target_score_array = pd.DataFrame(memory_grids_conditions.copy()).replace(target_score_translator).values  # target score for each subject

# Homogenise grid difficulty

# out = homogenise_grid_difficulty(n_rows, n_cols, ts_array, TARGET_SCORE_LEVEL, target_difficulty)

# out['max_diff'] = max_diff
# out['ts_array']= ts_array
# out['rew_array']= rew_array
