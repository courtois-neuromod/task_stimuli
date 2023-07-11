from os import environ
import numpy as np
import pandas as pd
import os
import argparse
from ast import literal_eval

if __name__ != "__main__":
    from ..tasks import robot, task_base

environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# Dimensions of a cell of the maze (1/8 of the maze's dimensions), in cm
CELL_HEIGHT = 110 / 8
CELL_WIDTH = 110 / 8


def get_tasks(parsed):
    n_tasks = 2
    order_df = pd.read_csv(
        f"data/robot/cozmofriends/sub-{parsed.subject}_ses-{parsed.session}_cozmofriends_pilot.csv"
    )
    for col in ["target_position", "winning_positions"]:
        order_df[col] = order_df[col].apply(literal_eval)
    for run in range(n_tasks):
        run_order_df = order_df[order_df["run"] == run + 1].sort_values("search_order")
        task = robot.CozmoFriends(
            source_id_imgs="cozmo_imgs_0",
            source_id_pos="neuromod_cozmo_tracking",
            source_id_actions="cozmo_actions_0",
            max_duration=15 * 60,
            target_names=run_order_df["target_name"].values,
            target_positions=run_order_df["winning_positions"].values,
            cell_width=CELL_WIDTH,
            cell_height=CELL_HEIGHT,
            target_imgs_dir="data/robot/cozmofriends",
            name=f"cozmofriends_run-{run+1:02d}",
            instruction="Explore the maze and find the target !",
        )
        yield task

        if task._task_completed:
            print("Task completed.")

        if run < n_tasks - 1:
            yield task_base.Pause(
                text="You can take a short break while we reset Cozmo.",
            )


def main(args):
    # Same permutation of position per session, different search order per run
    os.makedirs(args.out_dir, exist_ok=True)
    n_targets = len(TARGET_NAMES)
    rng = np.random.default_rng(args.subject)
    for ses in range(1, args.n_sessions + 1):
        orders = {
            "run": [],
            "search_order": [],
            "target_name": [],
            "target_position": [],
            "winning_positions": [],
        }
        pos_permutation = rng.permutation(n_targets)
        for run in range(1, args.n_runs + 1):
            search_order = rng.permutation(n_targets)
            for i, i_search in enumerate(search_order):
                orders["run"].append(run)
                orders["search_order"].append(i)
                orders["target_name"].append(TARGET_NAMES[i_search])
                position = list(TARGET_CELLS.keys())[pos_permutation[i_search]]
                orders["target_position"].append(position)
                orders["winning_positions"].append(TARGET_CELLS[position])
        df = pd.DataFrame.from_dict(orders)
        df.to_csv(
            os.path.join(
                args.out_dir,
                f"sub-{str(args.subject).zfill(2)}_ses-{str(ses).zfill(3)}_{args.tag}.csv",
            ),
            index=False,
        )


if __name__ == "__main__":
    TARGET_NAMES = [
        "Rachel",
        "Joey",
        "Monica",
        "Gunther",
        "Phoebe",
        "Chandler",
        "Ross",
        "Couch",
    ]

    TARGET_CELLS = {  # target pos: list of pos where target is visible
        (0, 0): [(0, 0), (0, 1)],
        (0, 3): [(0, 2), (0, 3)],
        (0, 4): [(0, 4), (0, 5)],
        (0, 7): [(0, 6), (0, 7)],
        (7, 0): [(7, 0), (7, 1)],
        (7, 3): [(7, 2), (7, 3)],
        (7, 4): [(7, 4), (7, 5)],
        (7, 7): [(7, 6), (7, 7)],
    }

    assert len(TARGET_NAMES) == len(
        TARGET_CELLS
    ), "Number of target names and target positions don't match."

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", dest="out_dir", type=str, help="Path to output dir.")
    parser.add_argument(
        "--n_ses", dest="n_sessions", type=int, help="How many sessions."
    )
    parser.add_argument(
        "--n_runs", dest="n_runs", type=int, help="How many runs per session."
    )
    parser.add_argument(
        "-s", dest="subject", type=int, help="Subject number (must be int)."
    )
    parser.add_argument(
        "-t", dest="tag", type=str, help="Tag to add in the output files names."
    )
    args = parser.parse_args()
    main(args)
