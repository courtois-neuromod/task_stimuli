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

if __name__ == "__main__":
    parsed = cli.parse_args()

    try:
        ses_mod = importlib.import_module('src.sessions.ses-%s'%parsed.session)
        tasks = ses_mod.TASKS
    except ImportError:
        raise(ValueError('session tasks file cannot be found for %s'%parsed.session))

    cli.main_loop(tasks, parsed.subject, parsed.session, parsed.eyetracking, parsed.fmri)
