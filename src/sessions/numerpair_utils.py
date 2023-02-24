import numpy as np
import pandas as pd
import random
from scipy.ndimage import label, generate_binary_structure


DIFFICULTY_SCALE = {
    3: 0,
    4: 0,
    5: 0.4,
    6: 0.5,
    7: 0.8571,
    8: 1,
}


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
        conditions (numpy.ndarray): array of condition permutations where the difference in trial index between repeats of each condition is maximised.
        max_condition_distance: maximum distance of conditions.
    """
    if contiguous:
        n_memory_grid = int(n_memory_grid / 2)

    conditions = []
    min_condition_distances = []
    for _ in range(n_samples):
        tmp_conditions = _generate_conditions(n_memory_grid, n_condition)
        conditions.append(tmp_conditions)
        min_condition_distances.append(_get_condition_distance(tmp_conditions, n_condition))

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


def homogenise_grid_difficulty(grid_size, target_score_array, target_score_levels):
    """Generates a set of permutations of pairs on an n_row x n_col grid with difficulty = target_difficulty.
    The same set of grids is generated for each participant and organised according to their individual sequence of
    target scores. The higher the score, the easier the grid.
    +1 is given to a pair's difficulty score if it is contiguous and +1 if it is vertically/horizontally aligned.

    Args:
        n_row (int): Number of rows in grid.
        n_col (int): Number of columns in grid.
        ts_array (ndarray): Trial array of target scores (assumes n_g == ts) (n_participants x n_memory_grid).
        ts_levels (list): List of target score levels.
        target_difficulty (list): The homogenous grid difficulty per TSLevel.

    Returns:
        grid_cell (list): A list of grids, where each element of the list is a tuple of a numpy array of grid location array, and a numpy array of grid difficulty array.
        index_array (ndarray): An array of indexes of each pair of locations in the grid for each trial, arranged
                               according to each participant's sequence of target scores.
    """
    n_row, n_col = grid_size
    n_pt, n_trials = target_score_array.shape
    n_ts_levels = len(target_score_levels)
    n_needed_pairs_per_level = [np.sum(target_score_array[0, :] == x) for x in target_score_levels]

    gridCell = pd.DataFrame(index=range(2), columns=range(3))
    permArrayTmp = np.zeros((n_trials, n_row * n_col))  # for checking no two grids are the same
    indexArray = np.full((n_trials, max(target_score_levels), 2, 2), np.nan)
    gridCounter = 0
    c = 0
    gridDiff = np.zeros((n_ts_levels, np.sum(n_needed_pairs_per_level)))

    # Loop through target score levels and generate enough valid trials
    valid_memory_grids = {}
    for n_pairs, needed_pairs in zip(target_score_levels, n_needed_pairs_per_level):
        # Generate all grids for nTSLvl
        current_grid_location = []
        current_grid_difficulty = []
        while len(current_grid_location) < needed_pairs:
            grid, difficulty_score = find_valid_grid(grid_size, n_pairs)
            # if grid already exist, disgard and find the next one
            if any(np.array_equal(c, grid) for c in current_grid_location):
                continue
            current_grid_location.append(grid)
            current_grid_difficulty.append(difficulty_score)
        valid_memory_grids[n_pairs] = current_grid_location, current_grid_difficulty

    # Permute grids according to task condition vector of each participant
    # TODO
    return

def find_valid_grid(grid_size, n_pairs, grid=None, difficulty_score_per_pair=(10, 10)):
    """
    Find valid grid that fits the difficulty level.
    """
    threshold = DIFFICULTY_SCALE[n_pairs]
    grid_difficulty_score = np.mean(difficulty_score_per_pair)
    if np.absolute(grid_difficulty_score - threshold) < 0.0001 \
        and np.sum(difficulty_score_per_pair == 2) < 3:
        print(f"Found grid containing {n_pairs} pairs of targets, at score {threshold}")
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
    location_index = range(grid_size[0] * grid_size[1])
    idx_number_pairs = random.sample(location_index, n_pairs * 2)  # 3 pairs means we need 6 locations
    memory_grid.flat[idx_number_pairs] = np.repeat(range(1, n_pairs + 1), 2)
    return memory_grid
