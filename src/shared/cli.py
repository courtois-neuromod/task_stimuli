import os
from psychopy import visual, logging, event

from src.shared import config, fmri, eyetracking

def main_loop(all_tasks, subject, session, enable_eyetracker=False, use_fmri=False):

    log_path = os.path.join(config.OUTPUT_DIR,  'sub-%s'%subject,'ses-%s'%session)
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)
    log_file = logging.LogFile(
        os.path.join(log_path, 'sub-%s_ses-%s.log'%(subject,session)),
        level=logging.INFO, filemode='w')

    ctl_win = visual.Window(**config.CTL_WINDOW)
    ctl_win.winHandle.set_caption('Stimuli')
    exp_win = visual.Window(**config.EXP_WINDOW)

    if enable_eyetracker:
        eyetracker = eyetracking.EyeTracker(
            ctl_win,
            roi=config.EYETRACKING_ROI,
            video_input="/dev/video1",
            detector='2d')
        eyetracker.start()

    # list of tasks to be ran in a session

    for task in all_tasks:

        # ensure to clear the screen if task aborted
        exp_win.flip()
        ctl_win.flip()

        use_eyetracking = False
        if enable_eyetracker and task.use_eyetracking:
            use_eyetracking = True

        #preload task files (eg. video)
        task.preload(exp_win)

        allKeys = []

        while True:

            for _ in task.run(exp_win, ctl_win):
                # check for global event keys
                allKeys = event.getKeys(['r','s','q'])
                if len(allKeys):
                    break
                if use_eyetracking:
                    eyetracker.draw_gazepoint(ctl_win)
                exp_win.flip()
                ctl_win.flip()
            else: # task completed
                break

            logging.flush()

            if not 'r' in allKeys:
                break
            exp_win.logOnFlip(
                level=logging.EXP,
                msg="task - %s: restart")
        task.unload()
        if 'q' in allKeys:
            print('quit')
            break
        print('skip')

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        prog='main.py',
        description=('Run all tasks in a session'),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--subject', '-s',
        help='Subject ID')
    parser.add_argument('--session', '-ss',
        help='Session ID')
    parser.add_argument('--fmri', '-f',
        help='Wait for fmri TTL to start each task',
        default=False)
    parser.add_argument('--eyetracking', '-e',
        help='Enable eyetracking',
        default=False)
    return parser.parse_args()
