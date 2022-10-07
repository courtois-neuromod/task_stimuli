# CLI: command line interface options and main loop

import os, datetime, traceback, glob, time
import itertools
from termcolor import colored, cprint
from collections.abc import Iterable, Iterator
from psychopy import core, visual, logging, event
import itertools

visual.window.reportNDroppedFrames = 10e10

TIMEOUT = 5
DELAY_BETWEEN_TASK = 2

globalClock = core.MonotonicClock(0)
logging.setDefaultClock(globalClock)

from . import config  # import first separately
from . import fmri, eyetracking, utils, meg, config
from ..tasks import task_base, video


def listen_shortcuts():
    if any([k[1] & event.MOD_CTRL for k in event._keyBuffer]):
        allKeys = event.getKeys(["n", "k", "q"], modifiers=True)
        ctrl_pressed = any([k[1]["ctrl"] for k in allKeys])
        all_keys_only = [k[0] for k in allKeys]
        if len(allKeys) and ctrl_pressed:
            return all_keys_only[0]
    return False


def run_task_loop(loop, eyetracker=None, gaze_drawer=None, record_movie=False):
    for frameN, _ in enumerate(loop):
        if gaze_drawer:
            gaze = eyetracker.get_gaze()
            if not gaze is None:
                gaze_drawer.draw_gazepoint(gaze)
        if record_movie and frameN % 6 == 0:
            record_movie.getMovieFrame(buffer="back")
        # check for global event keys
        shortcut_evt = listen_shortcuts()
        if shortcut_evt:
            return shortcut_evt


def run_task(
    task, exp_win, ctl_win=None, eyetracker=None, gaze_drawer=None, record_movie=False
):
    print("Next task: %s" % str(task))

    # show instruction
    shortcut_evt = run_task_loop(
        task.instructions(exp_win, ctl_win),
        eyetracker,
        gaze_drawer,
        record_movie=exp_win if record_movie else False,
    )

    if task.use_fmri and not shortcut_evt:
        for _ in fmri.wait_for_ttl():
            shortcut_evt = listen_shortcuts()
            if shortcut_evt:
                return shortcut_evt

    logging.info("GO")
    if eyetracker and not shortcut_evt and task.use_eyetracking:
        eyetracker.start_recording(task.name)
    # send start trigger/marker to MEG + Biopac (or anything else on parallel port)
    if task.use_meg and not shortcut_evt:
        meg.send_signal(meg.MEG_settings["TASK_START_CODE"])

    if not shortcut_evt:
        shortcut_evt = run_task_loop(
            task.run(exp_win, ctl_win),
            eyetracker,
            gaze_drawer,
            record_movie=exp_win if record_movie else False,
        )

    # send stop trigger/marker to MEG + Biopac (or anything else on parallel port)
    if task.use_meg and not shortcut_evt:
        meg.send_signal(meg.MEG_settings["TASK_STOP_CODE"])

    if eyetracker:
        eyetracker.stop_recording()

    run_task_loop(
        task.stop(exp_win, ctl_win),
        eyetracker,
        gaze_drawer,
        record_movie=exp_win if record_movie else False,
    )

    # now that time is less sensitive: save files
    task.save()

    return shortcut_evt


def main_loop(
    session_module,
    parsed,
):
    """    subject,
        output_ds,
        eyetracker=False,
        use_fmri=False,
        use_meg=False,
        show_ctl_win=False,
        allow_run_on_battery=False,
        enable_ptt=False,
        record_movie=False,
        skip_soundcheck=False,
        calibration_targets=False,
        validate_eyetrack=False,
        **kwargs
    ):"""

    # check power source, for laptop setup
    if not utils.check_power_plugged():
        cprint("*" * 25 + "WARNING: the power cord is not connected" + "*" * 25, 'red', attrs=['blink'])
        if not parsed.run_on_battery:
            return

    # get session specific config
    if hasattr(session_module, 'get_config'):
        session_config = session_module.get_config(parsed)
        #override some config parameters from the command line
        session_config.update({k:v for k,v in vars(parsed).items() if v})
        print(session_config)


    # get tasks subset
    all_tasks = session_module.get_tasks(parsed)

    if parsed.skip_n_tasks:
        if isinstance(all_tasks, Iterator):
            all_tasks = itertools.islice(all_tasks, parsed.skip_n_tasks, None)
        else:
            all_tasks = tasks[parsed.skip_n_tasks:]

    # setup output and filename templates
    if not parsed.output:
        parsed.output = os.path.join(os.environ["OUTPUT_PATH"], session_config['output_dataset'])

    print(f'outputs will be saved in {parsed.output}')
    bids_sub_ses = ("sub-%s" % parsed.subject, "ses-%s" % parsed.session)
    log_path = os.path.abspath(os.path.join(parsed.output, "sourcedata", *bids_sub_ses))
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)
    log_name_prefix = "sub-%s_ses-%s_%s" % (
        parsed.subject,
        parsed.session,
        datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
    )
    logfile_path = os.path.join(log_path, log_name_prefix + ".log")
    log_file = logging.LogFile(logfile_path, level=logging.INFO, filemode="w")

    # create windows for stimuli
    exp_win = visual.Window(**config.EXP_WINDOW, monitor=config.EXP_MONITOR)
    exp_win.mouseVisible = False
    if parsed.control_window:
        ctl_win = visual.Window(**config.CTL_WINDOW)
        ctl_win.name = "Stimuli"
    else:
        ctl_win = None

    # Create push-to-talk "controller"
    ptt = None
    if parsed.ptt:
        from .ptt import PushToTalk
        ptt = PushToTalk()

    if parsed.fmri:
        setup_video_path = utils.get_subject_soundcheck_video(parsed.subject)

        setup_tasks = [
        video.VideoAudioCheckLoop(
            setup_video_path,
            name="setup_soundcheck_video",) if not parsed.skip_soundcheck else None,
        task_base.Pause(
            """We are completing the setup and initializing the scanner.
We will start the tasks in a few minutes.
Please remain still."""
        )]

        all_tasks = itertools.chain(
            filter(bool,setup_tasks),
            all_tasks,
            [task_base.Pause(
                """We are done for today.
The scanner might run for a few seconds to acquire reference images.
Please remain still.
We are coming to get you out of the scanner shortly."""
            )],
        )

    # Initiliaze eyetracker client and start thread.
    eyetracker_client = None
    gaze_drawer = None
    if parsed.eyetracking:
        eyetracker_client = eyetracking.EyeTrackerClient(
            output_path=log_path,
            output_fname_base=log_name_prefix,
            profile=False,
            debug=False,
        )
        eyetracker_client.start()

        # append the eyetracker setup and all calibration/validations
        all_tasks = itertools.chain(
            [eyetracking.EyetrackerSetup(eyetracker=eyetracker_client, name='eyetracker_setup'),],
            all_tasks
        )
        all_tasks = eyetracker_client.interleave_calibration(
            all_tasks,
            calibration_version = session_config.get('eyetracking_calibration_version', 1),
            validation = session_config.get('eyetracking_validation',False),
            add_pauses = session_config.get('add_pauses', False),
            )

        if parsed.control_window:
            gaze_drawer = eyetracking.GazeDrawer(ctl_win)

    else:
        all_tasks = itertools.chain(
            all_tasks,
            [task_base.Pause(
                """We are done with the tasks for today.
Thanks for your participation!"""
            )],
        )

    if not isinstance(all_tasks, Iterator):

        # list of tasks to be ran in a session

        print("Here are the stimuli planned for today\n" + "_" * 50)
        for task in all_tasks:
            print(f"- {task.name} {getattr(task,'duration','')}" )
        print("_" * 50)

    try:
        for task in all_tasks:

            # clear events buffer in case the user pressed a lot of buttoons
            event.clearEvents()

            use_eyetracking = False
            if parsed.eyetracking and task.use_eyetracking:
                use_eyetracking = True

            # setup task files (eg. video)
            task.setup(
                exp_win,
                log_path,
                log_name_prefix,
                use_fmri=parsed.fmri,
                use_meg=parsed.meg,
            )
            print("READY")

            while True:
                # force focus on the task window to ensure getting keys, TTL, ...
                exp_win.winHandle.activate()
                # record frame intervals for debug

                shortcut_evt = run_task(
                    task,
                    exp_win,
                    ctl_win,
                    eyetracker_client,
                    gaze_drawer,
                    record_movie=parsed.record_movie,
                )

                if shortcut_evt == "n":
                    # restart the task
                    logging.exp(msg="task - %s: restart" % str(task))
                    task.restart()
                    continue
                elif shortcut_evt:
                    # abort/skip or quit
                    logging.exp(msg="task - %s: abort" % str(task))
                    break
                else:  # task completed
                    logging.exp(msg="task - %s: complete" % str(task))
                    # send stop trigger/marker to MEG + Biopac (or anything else on parallel port)
                    break

                logging.flush()
            if parsed.record_movie:
                out_fname = os.path.join(
                    task.output_path, "%s_%s.mp4" % (task.output_fname_base, task.name)
                )
                print(f"saving movie as {out_fname}")
                exp_win.saveMovieFrames(out_fname, fps=10)
            task.unload()

            if shortcut_evt == "q":
                print("quit")
                break
            elif shortcut_evt is None:
                # add a delay between tasks to avoid remaining TTL to start next task
                # do that only if the task was not aborted to save time
                # there is anyway the duration of the instruction before listening to TTL
                for i in range(DELAY_BETWEEN_TASK * config.FRAME_RATE):
                    exp_win.flip(clearBuffer=False)

        exp_win.saveFrameIntervals("exp_win_frame_intervals.txt")
        if ctl_win:
            ctl_win.saveFrameIntervals("ctl_win_frame_intervals.txt")

    except KeyboardInterrupt as ki:
        print(traceback.format_exc())
        logging.exp(msg="user killing the program")
        print("you killing me!")
    finally:
        if parsed.eyetracking:
            eyetracker_client.join(TIMEOUT)
