#!/usr/bin/python3

from psychopy import visual, logging # need to import visual first things to avoid pyglet related crash

from src.shared import config, fmri, eyetracking, cli
from src.tasks import images, video, memory, task_base

if __name__ == "__main__":
    parsed = cli.parse_args()

    all_tasks = [
    task_base.Pause("""Hi! We are setting up for the MRI session.
Make yourself comfortable.
Ensure that you can see the full screen and that the image is sharp."""),

        task_base.Pause("""We are about to start the MRI session.
Today you are going to watch videos.
Relax and please keep your eyes opened."""),

        video.SingleVideo(
            'data/videos/Inscapes_sound_normed.mp4', name='Inscapes',
            use_fmri=parsed.fmri, use_eyetracking=True),
        task_base.Pause(),
        video.SingleVideo(
            'data/videos/Oceans_fs_10m/Oceans_fs_10m_1.mp4',
            name='Oceans_chunk1',
            use_fmri=parsed.fmri, use_eyetracking=True),
        video.SingleVideo(
            'data/videos/Oceans_fs_10m/Oceans_fs_10m_2.mp4',
            name='Oceans_chunk1',
            use_fmri=parsed.fmri, use_eyetracking=True),
        video.SingleVideo(
            'data/videos/Oceans_fs_10m/Oceans_fs_10m_3.mp4',
            name='Oceans_chunk1',
            use_fmri=parsed.fmri, use_eyetracking=True),
        ]

    cli.main_loop(all_tasks, parsed.subject, parsed.session, parsed.eyetracking, parsed.fmri)
