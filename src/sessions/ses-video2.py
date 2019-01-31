from ..tasks import images, video, memory, task_base

TASKS = [

    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Inscapes_sound_normed.mp4', name='Inscapes'),
    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Inscapes_sound_normed.mp4', name='Inscapes'),

    task_base.Pause(),

    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Oceans_fs_10m_1.mp4',
        name='Oceans_fs_10m_4'),
    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Oceans_fs_10m_2.mp4',
        name='Oceans_fs_10m_5'),
    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Oceans_fs_10m_3.mp4',
        name='Oceans_fs_10m_6'),
    video.SingleVideo(
        'data/videos/Oceans_fs_10m/Oceans_fs_10m_3.mp4',
        name='Oceans_fs_10m_7'),

]
