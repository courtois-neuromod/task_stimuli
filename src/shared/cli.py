# CLI: command line interface options and main loop

import os, datetime, traceback, glob, time
from collections.abc import Iterable, Iterator
from psychopy import core, visual, logging, event
import itertools

visual.window.reportNDroppedFrames = 10e10

TIMEOUT = 5
DELAY_BETWEEN_TASK = 2

globalClock = core.MonotonicClock(0)
logging.setDefaultClock(globalClock)

from . import config  # import first separately
from . import fmri, eyetracking, utils, meg, eeg, config
from ..tasks import task_base, video


def listen_shortcuts():
    if any([k[1] & event.MOD_CTRL for k in event._keyBuffer]):
        allKeys = event.getKeys(["n", "c", "q"], modifiers=True)
        ctrl_pressed = any([k[1]["ctrl"] for k in allKeys])
        all_keys_only = [k[0] for k in allKeys]
        if len(allKeys) and ctrl_pressed:
            return all_keys_only[0]
    return False


def run_task_loop(task, loop, exp_win, eyetracker=None, gaze_drawer=None, record_movie=False):
    for frameN, _ in enumerate(loop):
        if gaze_drawer:
            gaze = eyetracker.get_gaze()
            if not gaze is None:
                gaze_drawer.draw_gazepoint(gaze)
        if task.use_meg and task._extra_markers:
            exp_win.callOnFlip(meg.send_signal, task._extra_markers)
        if task.use_eeg and task._extra_markers:
            exp_win.callOnFlip(eeg.send_signal, task._extra_markers)

        if record_movie and frameN % 6 == 0:
            record_movie.getMovieFrame(buffer="back")
        # check for global event keys
        shortcut_evt = listen_shortcuts()
        if shortcut_evt:
            return shortcut_evt
        # force regular flushing to keep log in case of hard crash
        if frameN % config.FRAME_RATE == 0:
            logging.flush()


def run_task(
    task, exp_win, ctl_win=None, eyetracker=None, gaze_drawer=None, record_movie=False
):
    print("Next task: %s" % str(task))

    # show instruction
    shortcut_evt = run_task_loop(
        task,
        task.instructions(exp_win, ctl_win),
        exp_win,
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
        exp_win.callOnFlip(meg.send_signal, meg.MEG_settings["TASK_START_CODE"])
    if task.use_eeg and not shortcut_evt:
        exp_win.callOnFlip(eeg.send_signal, eeg.EEG_settings["TASK_START_CODE"])

    try:
        if not shortcut_evt:
            shortcut_evt = run_task_loop(
                task,
                task.run(exp_win, ctl_win),
                eyetracker,
                gaze_drawer,
                record_movie=exp_win if record_movie else False,
            )

        # send stop trigger/marker to MEG + Biopac (or anything else on parallel port)
        if task.use_meg and not shortcut_evt:
            exp_win.callOnFlip(meg.send_signal, meg.MEG_settings["TASK_STOP_CODE"])
        if task.use_eeg and not shortcut_evt:
            exp_win.callOnFlip(eeg.send_signal, eeg.EEG_settings["TASK_STOP_CODE"])


        if eyetracker:
            eyetracker.stop_recording()

        run_task_loop(
            task,
            task.stop(exp_win, ctl_win),
            exp_win,
            eyetracker,
            gaze_drawer,
            record_movie=exp_win if record_movie else False,
        )

    except Exception as e:
        raise e
    finally: # attempt saving no matter what happened
        # now that time is less sensitive: save files
        task.save()

    return shortcut_evt


def main_loop(
    all_tasks,
    subject,
    session,
    output_ds,
    enable_eyetracker=False,
    use_fmri=False,
    use_meg=False,
    use_eeg=False,
    show_ctl_win=False,
    allow_run_on_battery=False,
    enable_ptt=False,
    record_movie=False,
    skip_soundcheck=False,
    calibration_targets=False,
    validate_eyetrack=False,
):

    # force screen resolution to solve issues with video splitter at scanner
    """xrandr = Popen([
        'xrandr',
        '--output', 'eDP-1',
        '--mode', '%dx%d'%config.EXP_WINDOW['size'],
        '--rate', str(config.FRAME_RATE)])
    time.sleep(5)"""

    if not utils.check_power_plugged():
        print("*" * 25 + "WARNING: the power cord is not connected" + "*" * 25)
        if not allow_run_on_battery:
            return

    bids_sub_ses = ("sub-%s" % subject, "ses-%s" % session)
    log_path = os.path.abspath(os.path.join(output_ds, "sourcedata", *bids_sub_ses))
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)
    log_name_prefix = "sub-%s_ses-%s_%s" % (
        subject,
        session,
        datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
    )
    logfile_path = os.path.join(log_path, log_name_prefix + ".log")
    log_file = logging.LogFile(logfile_path, level=logging.INFO, filemode="w")

    exp_win = visual.Window(**config.EXP_WINDOW, monitor=config.EXP_MONITOR)
    exp_win.mouseVisible = False

    if show_ctl_win:
        ctl_win = visual.Window(**config.CTL_WINDOW)
        ctl_win.name = "Stimuli"
    else:
        ctl_win = None

    ptt = None
    if enable_ptt:
        from .ptt import PushToTalk

        ptt = PushToTalk()

    eyetracker_client = None
    gaze_drawer = None
    if enable_eyetracker:
        print("creating et client")
        eyetracker_client = eyetracking.EyeTrackerClient(
            output_path=log_path,
            output_fname_base=log_name_prefix,
            profile=False,
            debug=False,
            use_targets = calibration_targets,
            validate_calib = validate_eyetrack,
        )
        print("starting et client")
        eyetracker_client.start()
        print("done")

        all_tasks = itertools.chain(
            [eyetracking.EyetrackerSetup(eyetracker=eyetracker_client, name='eyetracker_setup'),],
            all_tasks
        )
        all_tasks = eyetracker_client.interleave_calibration(all_tasks)

        if show_ctl_win:
            gaze_drawer = eyetracking.GazeDrawer(ctl_win)
    if use_fmri:

        all_tasks = itertools.chain(
            [task_base.Pause(
                """We are completing the setup and initializing the scanner.
We will start the tasks in a few minutes.
Please remain still."""
            )],
            all_tasks,
            [task_base.Pause(
                """We are done for today.
The scanner might run for a few seconds to acquire reference images.
Please remain still.
We are coming to get you out of the scanner shortly."""
            )],
        )

        if not skip_soundcheck:
            setup_video_path = utils.get_subject_soundcheck_video(subject)
            all_tasks = itertools.chain([
                task_base.Pause(
                    """Setup: we will soon run a soundcheck to check that the sensimetrics is adequately setup."""
                ),
                video.VideoAudioCheckLoop(setup_video_path, name="setup_soundcheck_video",)],
                all_tasks,
            )


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
            if enable_eyetracker and task.use_eyetracking:
                use_eyetracking = True

            # setup task files (eg. video)
            task.setup(
                exp_win,
                log_path,
                log_name_prefix,
                use_fmri=use_fmri,
                use_meg=use_meg,
                use_eeg=use_eeg,
            )
            print("READY")

            while True:
                # force focus on the task window to ensure getting keys, TTL, ...
                exp_win.winHandle.activate()
                # record frame intervals for debug

                try:
                    shortcut_evt = run_task(
                        task,
                        exp_win,
                        ctl_win,
                        eyetracker_client,
                        gaze_drawer,
                        record_movie=record_movie,
                    )
                except Exception:
                    task
                logging.flush()

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


            if record_movie:
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
                    exp_win.flip(clearBuffer=i<2)

        exp_win.saveFrameIntervals("exp_win_frame_intervals.txt")
        if ctl_win:
            ctl_win.saveFrameIntervals("ctl_win_frame_intervals.txt")

    except (KeyboardInterrupt, SystemExit) as ki:
        print(traceback.format_exc())
        logging.exp(msg="user killing the program")
        logging.flush()
        print("you killing me!")

        # Reset triggers to 0
        if task.use_meg:
            meg.send_signal(0)
        if task.use_eeg:
            eeg.send_signal(0)

    finally:
        if enable_eyetracker:
            eyetracker_client.join(TIMEOUT)
