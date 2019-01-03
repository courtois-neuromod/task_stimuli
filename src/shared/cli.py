import os, datetime
from psychopy import visual, logging, event

from src.shared import config, fmri, eyetracking

def main_loop(all_tasks, subject, session, enable_eyetracker=False, use_fmri=False):

    log_path = os.path.abspath(os.path.join(config.OUTPUT_DIR,  'sub-%s'%subject,'ses-%s'%session))
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)
    logfile_path = os.path.join(log_path, 'sub-%s_ses-%s_%s.log'%(subject,session,
                                datetime.datetime.now().strftime('%Y%m%d_%H%M%S')))
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
            )
        eyetracker_client.start()
        all_tasks.insert(0, eyetracking.EyetrackerCalibration(eyetracker_client,name='EyeTracker-Calibration'))
        gaze_drawer = eyetracking.GazeDrawer(exp_win)


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
        print('READY')

        allKeys = []

        while True:

            for _ in task.run(exp_win, ctl_win):
                if use_eyetracking:
                    gaze = eyetracker_client.get_gaze()
                    if not gaze is None:
                        gaze_drawer.draw_gazepoint(gaze)
                # check for global event keys
                exp_win.flip()
                ctl_win.flip()
                allKeys = event.getKeys(['r','s','q'])
                if len(allKeys):
                    break

            else: # task completed
                break

            logging.flush()
            task.stop()

            exp_win.flip()
            ctl_win.flip()

            if not 'r' in allKeys:
                break
            logging.exp(msg="task - %s: restart"%str(task))

        task.unload()
        if 'q' in allKeys:
            if enable_eyetracker:
                eyetracker_client.join()
                eye_video_file = os.path.join(log_path, 'eye0.mp4')
                timestamps_file = os.path.join(log_path, 'eye0_timestamps.npy')
                # rename file in case we rerun the software
                os.rename(eye_video_file, logfile_path[:-4] + '_eye0.mp4')
                os.rename(timestamps_file, logfile_path[:-4] + '_eye0_timestamps.npy')
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
