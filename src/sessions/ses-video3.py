from ..tasks import images, video, memory, task_base

TASKS = [
    task_base.Pause("""Hi! We are setting up for the MRI session.
Make yourself comfortable.
Ensure that you can see the full screen and that the image is sharp."""),

    task_base.Pause("""We are about to start the MRI session.
Today you are going to watch videos.
Relax and please keep your eyes opened."""),

    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Inscapes_sound_normed.mp4', name='Inscapes'),
    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Inscapes_sound_normed.mp4', name='Inscapes'),

    task_base.Pause(),

    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Oceans_fs_10m_1.mp4',
        name='Oceans_fs_10m_8'),
    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Oceans_fs_10m_2.mp4',
        name='Oceans_fs_10m_9'),
    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Oceans_fs_10m_3.mp4',
        name='Oceans_fs_10m_10'),
    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Oceans_fs_10m_3.mp4',
        name='Oceans_fs_10m_11'),

    task_base.Pause("""We are done for today.
Relax, we are coming to get you out of the scanner in a short time."""),
]
