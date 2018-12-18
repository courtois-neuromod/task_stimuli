#!/usr/bin/python3

from psychopy import visual, logging # need to import visual first things to avoid pyglet related crash

from src.shared import config, fmri, eyetracking, cli
from src.tasks import images, video, memory, task_base

if __name__ == "__main__":
    parsed = cli.parse_args()

    all_tasks = [
        video.SingleVideo(
            'data/videos/Inscapes-67962604.mp4', name='Inscapes',
            use_fmri=parsed.fmri, use_eyetracking=True),
        task_base.Pause(),
        # source: https://drive.google.com/file/d/1prOM1QuPEAcqe_D-3rLYNu937A8VzbsB/view
        video.SingleVideo(
            'data/videos/tammy/Oceans_1.mp4',
            name='Oceans_chunk1',
            use_fmri=parsed.fmri, use_eyetracking=True),
        ]

    cli.main_loop(all_tasks, parsed.subject, parsed.session, parsed.eyetracking, parsed.fmri)
