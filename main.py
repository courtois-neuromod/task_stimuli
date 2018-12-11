#!/usr/bin/python3

from psychopy import visual, logging, event

from src.shared import config, fmri, eyetracking, cli
from src.tasks import images, video, memory, task_base

def main_loop(all_tasks, subject, session, enable_eyetracker=False, use_fmri=False):
    ctl_win = visual.Window(**config.CTL_WINDOW)
    exp_win = visual.Window(**config.EXP_WINDOW)

    if enable_eyetracker:
        roi = eyetracking.Roi(config.EYETRACKING_ROI[-1])
        roi.set(config.EYETRACKING_ROI)
        eyetracker = eyetracking.EyeTracker(
            ctl_win,
            roi=roi,
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
            print('restart')
        task.unload()
        if 'q' in allKeys:
            print('quit')
            break
        print('skip')


if __name__ == "__main__":
    parsed = cli.parse_args()
    lastLog = logging.LogFile("lastRun.log", level=logging.INFO, filemode='w')

    all_tasks = [
        #eyetracking.EyetrackerCalibration(eyetracker),
        #memory.ImagePosition('data/memory/stimuli.csv', use_fmri=parsed.fmri, use_eyetracking=True),
        video.SingleVideo('data/videos/Inscapes-67962604.mp4',use_fmri=parsed.fmri, use_eyetracking=True),
        task_base.Pause(),
        video.SingleVideo('data/videos/skateboard_fails.mp4',use_fmri=parsed.fmri, use_eyetracking=True),
        images.Images('data/images/test_conditions.csv',use_fmri=parsed.fmri, use_eyetracking=True)
        ]

    cli.main_loop(all_tasks, parsed.subject, parsed.session, parsed.eyetracking, parsed.fmri)
