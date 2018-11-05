from psychopy import visual, logging

from src.shared import config, fmri, eyetracking
from src.tasks import images, video

def main():
    ctl_win = visual.Window(**config.CTL_WINDOW)
    exp_win = visual.Window(**config.EXP_WINDOW)

    if config.EYETRACKING:
        roi = eyetracking.Roi((560,420))
        roi.set((40,30,600,450,(560,420)))
        eyetracker = eyetracking.EyeTracker(ctl_win,roi=roi,video_input="/dev/video1")
        eyetracker.start()
        #TODO: setup stuff here

    all_tasks = [
        eyetracking.EyetrackerCalibration(eyetracker),
        video.SingleVideo('data/videos/Inscapes-67962604.mp4',use_fmri=True, use_eyetracking=True),
        images.Images('data/images/test_conditions.csv',use_fmri=True, use_eyetracking=True)
        ]

    for task in all_tasks:
        use_eyetracking = False
        if config.EYETRACKING and task.use_eyetracking:
            use_eyetracking = True
            #eyetracker.draw_gazepoint(exp_win)
        if hasattr(task, 'instructions'):
            for _ in task.instructions(ctl_win, ctl_win):
                exp_win.flip()
                ctl_win.flip()

        if task.use_fmri:
            while True:
                if fmri.get_ttl():
                    #TODO: log real timing of TTL?
                    exp_win.logOnFlip(
                        level=logging.EXP,
                        msg="fMRI TTL")
                    break
                if use_eyetracking:
                    eyetracker.draw_gazepoint(exp_win)
                exp_win.flip()
                ctl_win.flip()

        for _ in task.run(exp_win, ctl_win):
            if use_eyetracking:
                eyetracker.draw_gazepoint(exp_win)
            exp_win.flip()
            ctl_win.flip()
        logging.flush()

if __name__ == "__main__":
    lastLog = logging.LogFile("lastRun.log", level=logging.INFO, filemode='w')
    main()
