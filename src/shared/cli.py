# CLI: command line interface options and main loop

import os, datetime, traceback, glob
from psychopy import core, visual, logging, event

TIMEOUT = 5
DELAY_BETWEEN_TASK = 5

globalClock = core.MonotonicClock(0)
logging.setDefaultClock(globalClock)

from . import config #import first separately
from . import fmri, eyetracking, utils, meg
from ..tasks import task_base, video


def listen_shortcuts():
    if any([k[1]&event.MOD_CTRL for k in event._keyBuffer]):
        allKeys = event.getKeys(['n','c','q'], modifiers=True)
        ctrl_pressed = any([k[1]['ctrl'] for k in allKeys])
        all_keys_only = [k[0] for k in allKeys]
        if len(allKeys) and ctrl_pressed:
            return all_keys_only[0]
    return False

def run_task_loop(loop, eyetracker=None, gaze_drawer=None):
    for _ in loop:
        if gaze_drawer:
            gaze = eyetracker_client.get_gaze()
            if not gaze is None:
                gaze_drawer.draw_gazepoint(gaze)
        # check for global event keys
        shortcut_evt = listen_shortcuts()
        if shortcut_evt:
            return shortcut_evt

def run_task(task, exp_win, ctl_win=None, eyetracker=None, gaze_drawer=None):
    print('Next task: %s'%str(task))

    # show instruction
    shortcut_evt = run_task_loop(task.instructions(exp_win, ctl_win), eyetracker, gaze_drawer)
    if shortcut_evt: return shortcut_evt

    if task.use_fmri:
        shortcut_evt = run_task_loop(fmri.wait_for_ttl(), eyetracker, gaze_drawer)
        if shortcut_evt: return shortcut_evt

    logging.info('GO')

    # send start trigger/marker to MEG + Biopac (or anything else on parallel port)
    if task.use_meg:
        meg.send_signal(meg.MEG_settings['TASK_START_CODE'])

    shortcut_evt = run_task_loop(task.run(exp_win, ctl_win), eyetracker, gaze_drawer)

    # send stop trigger/marker to MEG + Biopac (or anything else on parallel port)
    if task.use_meg:
        meg.send_signal(meg.MEG_settings['TASK_STOP_CODE'])

    # now that time is less sensitive: save files
    task.save()

    return shortcut_evt

def main_loop(all_tasks,
    subject,
    session,
    enable_eyetracker=False,
    use_fmri=False,
    use_meg=False,
    show_ctl_win=False,
    allow_run_on_battery=False,
    enable_ptt=False):

    if not utils.check_power_plugged():
        print('*'*25+'WARNING: the power cord is not connected'+'*'*25)
        if not allow_run_on_battery:
            return

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


    ptt = None
    if enable_ptt:
        from .ptt import PushToTalk
        ptt = PushToTalk()

    gaze_drawer = None
    if enable_eyetracker:
        print('creating et client')
        eyetracker_client = eyetracking.EyeTrackerClient(
            output_path=log_path,
            output_fname_base=log_name_prefix
            )
        print('starting et client')
        eyetracker_client.start()
        print('done')
        all_tasks.insert(0, eyetracking.EyetrackerCalibration(eyetracker_client, name='EyeTracker-Calibration'))
        if show_ctl_win:
            gaze_drawer = eyetracking.GazeDrawer(ctl_win)
    if use_fmri:
        setup_video_path = glob.glob(os.path.join('data','videos','subject_setup_videos','sub-%s_*'%subject))
        if not len(setup_video_path):
            setup_video_path = [os.path.join('data','videos','subject_setup_videos','sub-default_setup_video.mp4')]

        all_tasks.insert(0, video.VideoAudioCheckLoop(setup_video_path[0], name='setup_soundcheck_video'))
        all_tasks.insert(1, task_base.Pause("""We are completing the setup and initializing the scanner.
We will start the tasks in a few minutes.
Please remain still."""))
        all_tasks.append(task_base.Pause("""We are done for today.
The scanner might run for a few seconds to acquire reference images.
Please remain still.
We are coming to get you out of the scanner shortly."""))
    else:
        all_tasks.append(task_base.Pause("""We are done with the tasks for today.
Thanks for your participation!"""))
    # list of tasks to be ran in a session

    print('Here are the stimuli planned for today\n' + '_'*50)
    for task in all_tasks:
        print('- ' + task.name)
    print('_'*50)

    try:
        for task in all_tasks:

            #clear events buffer in case the user pressed a lot of buttoons
            event.clearEvents()

            use_eyetracking = False
            if enable_eyetracker and task.use_eyetracking:
                use_eyetracking = True

            #setup task files (eg. video)
            task.setup(exp_win, log_path, log_name_prefix,
                use_fmri=use_fmri,
                use_eyetracking=use_eyetracking,
                use_meg=use_meg)
            print('READY')

            while True:
                #force focus on the task window to ensure getting keys, TTL, ...
                exp_win.winHandle.activate()
                # record frame intervals for debug
                exp_win.recordFrameIntervals = True

                shortcut_evt = run_task(task, exp_win, ctl_win, gaze_drawer)

                if shortcut_evt == 'n':
                    # restart the task
                    logging.exp(msg="task - %s: restart"%str(task))
                    task.restart()
                    continue
                elif shortcut_evt:
                    # abort/skip or quit
                    logging.exp(msg="task - %s: abort"%str(task))
                    break
                else: # task completed
                    logging.exp(msg="task - %s: complete"%str(task))
                    # send stop trigger/marker to MEG + Biopac (or anything else on parallel port)
                    break

                logging.flush()
                task.stop()

            task.unload()
            exp_win.recordFrameIntervals = True
            exp_win.saveFrameIntervals('frame_intervals.txt')

            if shortcut_evt=='q':
                print('quit')
                break
            elif shortcut_evt is None:
                # add a delay between tasks to avoid remaining TTL to start next task
                # do that only if the task was not aborted to save time
                # there is anyway the duration of the instruction before listening to TTL
                for i in range(DELAY_BETWEEN_TASK*config.FRAME_RATE):
                    exp_win.flip(clearBuffer=False)

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
    parser.add_argument('--meg', '-m',
        help='Send signal to parallel port to start trigger to MEG and Biopac.',
        action='store_true')
    parser.add_argument('--eyetracking', '-e',
        help='Enable eyetracking',
        action='store_true')
    parser.add_argument('--skip_n_tasks',
        help='skip n of the tasks',
        default=0,
        type=int)
    parser.add_argument('--ctl_win',
        help='show control window',
        action='store_true')
    parser.add_argument('--run_on_battery',
        help='allow the script to run on battery',
        action='store_true')
    parser.add_argument('--ptt',
        help='enable Push-To-Talk function',
        action='store_true')
    return parser.parse_args()
