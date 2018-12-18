#!/usr/bin/python3

from psychopy import visual, logging # need to import visual first things to avoid pyglet related crash

from src.shared import config, fmri, eyetracking, cli
from src.tasks import images, video, memory, task_base

if __name__ == "__main__":
    parsed = cli.parse_args()

    all_tasks = [
        #memory.ImagePosition('data/memory/stimuli.csv', use_fmri=parsed.fmri, use_eyetracking=True),
        video.SingleVideo(
            'data/videos/Inscapes-67962604.mp4', name='Inscapes',
            use_fmri=parsed.fmri, use_eyetracking=True),
        task_base.Pause(),
        video.SingleVideo(
            'data/videos/skateboard_fails.mp4',
            name='skateboard_fails',
            use_fmri=parsed.fmri, use_eyetracking=True),
        images.Images(
            'data/images/test_conditions.csv',
            name='bold5000',
            use_fmri=parsed.fmri, use_eyetracking=True)
        ]

    cli.main_loop(all_tasks, parsed.subject, parsed.session, parsed.eyetracking, parsed.fmri)
