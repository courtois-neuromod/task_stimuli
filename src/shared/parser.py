import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=("Run all tasks in a session"),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--subject", "-s", required=True, help="Subject ID")
    parser.add_argument("--session", "-ss", required=True, help="Session")
    parser.add_argument("--tasks", "-t", required=True, help="tasks set")
    parser.add_argument("--output", "-o", required=True, help="output dataset")
    parser.add_argument(
        "--fmri", "-f", help="Wait for fmri TTL to start each task", action="store_true"
    )
    parser.add_argument(
        "--meg",
        "-m",
        help="Send signal to parallel port to start trigger to MEG and Biopac.",
        action="store_true",
    )
    parser.add_argument(
        "--eyetracking", "-e", help="Enable eyetracking", action="store_true"
    )
    parser.add_argument(
        "--skip_n_tasks", help="skip n of the tasks", default=0, type=int
    )
    parser.add_argument("--ctl_win", help="show control window", action="store_true")
    parser.add_argument(
        "--run_on_battery",
        help="allow the script to run on battery",
        action="store_true",
    )
    parser.add_argument(
        "--ptt", help="enable Push-To-Talk function", action="store_true"
    )
    parser.add_argument("--profile", help="enable profiling", action="store_true")
    parser.add_argument(
        "--record-movie", help="record a movie of each task", action="store_true"
    )
    return parser.parse_args()
