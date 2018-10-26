from psychopy import visual

from shared import config, fmri

import image_task

def main():
    ctl_win = visual.Window(**config.CTL_WINDOW)
    exp_win = visual.Window(**config.EXP_WINDOW)

    tasks = []


if __name__ == "__main__":
    main()
