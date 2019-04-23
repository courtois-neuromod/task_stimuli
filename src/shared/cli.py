import os, datetime, traceback, glob
from psychopy import core, visual, logging, event

TIMEOUT = 5

globalClock = core.MonotonicClock(0)
logging.setDefaultClock(globalClock)

from . import config, fmri, eyetracking
from ..tasks import task_base, video

def main_loop(all_tasks, subject, session, enable_eyetracker=False, use_fmri=False, show_ctl_win = False):

    log_path = os.path.abspath(os.path.join(config.OUTPUT_DIR,  'sub-%s'%subject,'ses-%s'%session))
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)
    log_name_prefix = 'sub-%s_ses-%s_%s'%(subject,session, datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    logfile_path = os.path.join(log_path, log_name_prefix+'.log')
    log_file = logging.LogFile(
        logfile_path,
        level=logging.INFO, filemode='w')

    if show_ctl_win:
        ctl_win = visual.Window(**config.CTL_WINDOW)
        ctl_win.winHandle.set_caption('Stimuli')
    else:
        ctl_win = None
    exp_win = visual.Window(**config.EXP_WINDOW)
    exp_win.mouseVisible = False

    if enable_eyetracker:
        print('creating et client')
        eyetracker_client = eyetracking.EyeTrackerClient(
            output_path=log_path,
            output_fname_base=log_name_prefix
            )
        print('starting et client')
        eyetracker_client.start()
        print('done')
        #all_tasks.insert(0, eyetracking.EyetrackerCalibration(eyetracker_client,name='EyeTracker-Calibration'))
        gaze_drawer = eyetracking.GazeDrawer(ctl_win)
    if use_fmri:
        setup_video_path = glob.glob(os.path.join('data','videos','subject_setup_videos','sub-%s_*'%subject))
        if not len(setup_video_path):
            setup_video_path = [os.path.join('data','videos','subject_setup_videos','sub-default_setup_video.mp4')]
        all_tasks.append(task_base.Pause("""We are completing the setup and initializing the scanner.
We will start the tasks in a few minutes.
Please remain still."""))
        all_tasks.insert(0, video.VideoAudioCheckLoop(setup_video_path[0], name='setup_video'))
        all_tasks.append(task_base.Pause("""We are done for today.
The scanner might run for a few seconds to acquire reference images.
Please remain still.
We are coming to get you out of the scanner shortly."""))
    else:
        all_tasks.append(task_base.Pause("""We are done with the tasks for today.
Thanks for your participation!"""))
    # list of tasks to be ran in a session

    try:
        for task in all_tasks:

            #clear events buffer in case the user pressed a lot of buttoons
            event.clearEvents()
            # ensure to clear the screen if task aborted
            exp_win.flip()
            if show_ctl_win:
                ctl_win.flip()

            use_eyetracking = False
            if enable_eyetracker and task.use_eyetracking:
                use_eyetracking = True

            #setup task files (eg. video)
            task.setup(exp_win, log_path, log_name_prefix, use_fmri=use_fmri, use_eyetracking=use_eyetracking)
            print('READY')

            allKeys = []
            ctrl_pressed = False

            while True:
                #force focus on the task window to ensure getting keys, TTL, ...
                exp_win.winHandle.activate()

                for draw in task.run(exp_win, ctl_win):

                    if use_eyetracking:
                        gaze = eyetracker_client.get_gaze()
                        if not gaze is None:
                            gaze_drawer.draw_gazepoint(gaze)
                    # check for global event keys
                    exp_win.flip()
                    if show_ctl_win:
                        ctl_win.flip()

                    if any([k[1]&event.MOD_CTRL for k in event._keyBuffer]):
                        allKeys = event.getKeys(['n','c','q'], modifiers=True)
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

                # ensure last frame or task clear is draw
                exp_win.flip()
                if show_ctl_win:
                    ctl_win.flip()

                if ctrl_pressed and ('c' in all_keys_only or 'q' in all_keys_only):
                    break
                logging.exp(msg="task - %s: restart"%str(task))
                task.restart()
            task.unload()
            if ctrl_pressed and ('q' in all_keys_only):
                print('quit')
                break
            print('skip')

    except KeyboardInterrupt as ki:
        print(traceback.format_exc())
        logging.exp(msg="user killing the program")
        print('you killing me!')
    finally:
        if enable_eyetracker:
            eyetracker_client.join(TIMEOUT)

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
        action='store_true')
    parser.add_argument('--eyetracking', '-e',
        help='Enable eyetracking',
        action='store_true')
    return parser.parse_args()
