#!/usr/bin/python3
from subprocess import Popen

import os, sys, importlib
import itertools
from collections.abc import Iterable, Iterator

from src.shared import config
from src.shared import parser, screen
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
    if parsed.skip_n_tasks:
        if isinstance(tasks, Iterator):
            tasks = itertools.islice(tasks, parsed.skip_n_tasks, None)
        else:
            tasks = tasks[parsed.skip_n_tasks:]
    try:
        cli.main_loop(
            tasks,
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
            parsed.skip_soundcheck,
            parsed.target_ETcalibration,
            parsed.validate_ET,                        
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
    # parsed = parser.parse_args()
    # if parsed.profile:
    #     run_profiled(parsed)
    # else:
    #     run(parsed)

    from src.tasks.multfs_dms import multfs_dms
    from src.tasks.multfs_1back import multfs_1back
    from src.tasks.multfs_ctx import multfs_ctx
    from psychopy.visual import Window

    # please change the imagefolder name in the corresponding task file
    # dms
    item_list = "./data/multfs/DMS_loc_4stim.csv"
    task = multfs_dms(item_list, name = "multfs_dms_loc")
    exp_win = Window(size=(800, 800), fullscr=False,)
    task.setup(exp_win)
    task.run(exp_win, ctl_win = None)

    # 1back
    # item_list = "/Users/xiaoxuanlei/Desktop/202209_MULTFS_mri/202209_MULTFS_MRI_Simple/tasks/1back_loc/1back_loc_4stim_seq6.csv"
    # task = multfs_1back(item_list, name="multfs_1back_loc")
    # exp_win = Window(size=(800, 800), fullscr=False, )
    # task.setup(exp_win)
    # task.run(exp_win, ctl_win=None)

    # ctx
    # ['col', 'olc', 'loc', 'lco']
    # item_list = "/Users/xiaoxuanlei/Desktop/202209_MULTFS_mri/202209_MULTFS_MRI_Simple/tasks/CTX_category_object_loc_stim4.csv"
    # task = multfs_ctx(item_list, name = "multfs_ctx_col")
    # exp_win = Window(size=(800, 800), fullscr=False,)
    # task.setup(exp_win)
    # task.run(exp_win, ctl_win = None)
