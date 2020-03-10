#!/usr/bin/python3
import os, sys, importlib
from psychopy import visual, logging # need to import visual first things to avoid pyglet related crash

# threading and processing
from multiprocessing import (
    Process,
    Value,
    active_children,
    set_start_method,
    freeze_support,
)

from src.shared import cli

def run(parsed):
    try:
        ses_mod = importlib.import_module('src.sessions.ses-%s'%parsed.session)
        tasks = ses_mod.TASKS
    except ImportError:
        raise(ValueError('session tasks file cannot be found for %s'%parsed.session))
    cli.main_loop(
        tasks[parsed.skip_n_tasks:],
        parsed.subject,
        parsed.session,
        parsed.eyetracking,
        parsed.fmri,
        parsed.meg,
        parsed.ctl_win,
        parsed.run_on_battery,
        parsed.ptt)

def run_profiled(parsed):
    import cProfile
    from main import run
    cProfile.runctx(
        "run(parsed)",
        {'parsed':parsed},
        locals(),
        "task_stimuli.pstats"
    )

if __name__ == "__main__":
    parsed = cli.parse_args()
    if parsed.profile:
        run_profiled(parsed)
    else:
        run(parsed)
