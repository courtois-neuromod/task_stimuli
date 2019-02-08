from ..tasks import images, video, memory, task_base

TASKS = [

    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Inscapes_sound_normed.mp4', name='Inscapes'),
    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Inscapes_sound_normed.mp4', name='Inscapes'),

    task_base.Pause(),

    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Oceans_fs_10m_8.mp4',
        name='Oceans_fs_10m_8'),
    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Oceans_fs_10m_9.mp4',
        name='Oceans_fs_10m_9'),
    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Oceans_fs_10m_10.mp4',
        name='Oceans_fs_10m_10'),
    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Oceans_fs_10m_11.mp4',
        name='Oceans_fs_10m_11'),

]
