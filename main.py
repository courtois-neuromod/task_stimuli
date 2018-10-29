from psychopy import visual

from shared import config, fmri, eyetracking


import tasks.images

def main():
    ctl_win = visual.Window(**config.CTL_WINDOW)
    exp_win = visual.Window(**config.EXP_WINDOW)

    all_tasks = [tasks.images.Image(use_fmri=True, use_eyetracking=True)]

    for task in all_tasks:

        if hasattr(task, 'instructions'):
            for _ in task.instructions(exp_win, ctl_win):
                exp_win.flip()
                ctl_win.flip()
        use_eyetracking = False
        if task.use_eyetracking:
            use_eyetracking = True
            eyetracker = eyetracking.EyeTracker(ctl_win)
            #TODO: setup stuff here
        if task.use_fmri:
            fmri.wait_for_ttl(exp_win)
        for _ in task.run(exp_win, ctl_win):
            if use_eyetracking:
                pupils = eyetracker.update()
            exp_win.flip()
            ctl_win.flip()

if __name__ == "__main__":
    main()
