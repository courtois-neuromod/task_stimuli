#!/usr/bin/python3
from subprocess import Popen

import os, sys, importlib

from src.shared import parser, config, screen
from src.shared.didyoumean import suggest_session_tasks


def run(parsed):
    # initializing the screen need to be done before loading any psychopy
    if not parsed.no_force_resolution:
        screen.init_exp_screen()
    try:
        ses_mod = importlib.import_module('src.sessions.ses-%s'%parsed.tasks)
        tasks = ses_mod.get_tasks(parsed) if hasattr(ses_mod, 'get_tasks') else ses_mod.TASKS
    except ImportError:
        suggestion = suggest_session_tasks(parsed.tasks)
        raise(ValueError('session tasks file cannot be found for %s. Did you mean %s ?'%(parsed.tasks, suggestion)))
    from src.shared import cli
    try:
        cli.main_loop(
            tasks[parsed.skip_n_tasks:],
            parsed.subject,
            parsed.session,
            parsed.output,
            parsed.eyetracking,
            parsed.fmri,
            parsed.meg,
            parsed.ctl_win,
            parsed.run_on_battery,
            parsed.ptt,
            parsed.record_movie,
            )
    finally:
        if not parsed.no_force_resolution:
            screen.reset_exp_screen()

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
    parsed = parser.parse_args()
    if parsed.profile:
        run_profiled(parsed)
    else:
        run(parsed)
