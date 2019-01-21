import os, datetime
from psychopy import core, visual, logging, event

globalClock = core.MonotonicClock(0)
logging.setDefaultClock(globalClock)

from src.shared import config, fmri, eyetracking

def main_loop(all_tasks, subject, session, enable_eyetracker=False, use_fmri=False):

    log_path = os.path.abspath(os.path.join(config.OUTPUT_DIR,  'sub-%s'%subject,'ses-%s'%session))
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)
    log_name_prefix = 'sub-%s_ses-%s_%s'%(subject,session, datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    logfile_path = os.path.join(log_path, log_name_prefix+'.log')
    log_file = logging.LogFile(
        logfile_path,
        level=logging.INFO, filemode='w')

    ctl_win = visual.Window(**config.CTL_WINDOW)
    ctl_win.winHandle.set_caption('Stimuli')
    exp_win = visual.Window(**config.EXP_WINDOW)
    exp_win.mouseVisible = False

    if enable_eyetracker:
        eyetracker_client = eyetracking.EyeTrackerClient(
            output_path=log_path,
            output_fname_base=log_name_prefix
            )
        eyetracker_client.start()
        all_tasks.insert(0, eyetracking.EyetrackerCalibration(eyetracker_client,name='EyeTracker-Calibration'))
        gaze_drawer = eyetracking.GazeDrawer(ctl_win)


    # list of tasks to be ran in a session

    for task in all_tasks:

        # ensure to clear the screen if task aborted
        exp_win.flip()
        ctl_win.flip()

        use_eyetracking = False
        if enable_eyetracker and task.use_eyetracking:
            use_eyetracking = True

        #setup task files (eg. video)
        task.setup(exp_win, log_path, log_name_prefix)
        print('READY')

        allKeys = []
        ctrl_pressed = False

        while True:

            for _ in task.run(exp_win, ctl_win):
                if use_eyetracking:
                    gaze = eyetracker_client.get_gaze()
                    if not gaze is None:
                        gaze_drawer.draw_gazepoint(gaze)
                # check for global event keys
                exp_win.flip()
                ctl_win.flip()
                allKeys = event.getKeys(['n','s','q'], modifiers=True)
                ctrl_pressed = any([k[1]['ctrl'] for k in allKeys])
                all_keys_only = [k[0] for k in allKeys]
                if len(allKeys) and ctrl_pressed:
                    break
            else: # task completed
                task.save()
                break
            task.save()

            logging.flush()
            task.stop()

            exp_win.flip()
            ctl_win.flip()

            if ctrl_pressed and ('s' in all_keys_only or 'q' in all_keys_only):
                break
            logging.exp(msg="task - %s: restart"%str(task))

        task.unload()
        if ctrl_pressed and ('q' in all_keys_only):
            if enable_eyetracker:
                eyetracker_client.join()
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
