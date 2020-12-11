from ..tasks import images, video, memory, task_base

TASKS = [
    video.SingleVideo(
        "data/videos/Oceans_fs_10m_filt/Inscapes_sound_normed_filt.mp4", name="Inscapes"
    ),
    video.SingleVideo(
        "data/videos/Oceans_fs_10m_filt/Inscapes_sound_normed_filt.mp4", name="Inscapes"
    ),
    task_base.Pause(),
    video.SingleVideo(
        "data/videos/Oceans_fs_10m_filt/Oceans_fs_10m_1_filt.mp4",
        name="Oceans_fs_10m_1",
    ),
    video.SingleVideo(
        "data/videos/Oceans_fs_10m_filt/Oceans_fs_10m_2_filt.mp4",
        name="Oceans_fs_10m_2",
    ),
    video.SingleVideo(
        "data/videos/Oceans_fs_10m_filt/Oceans_fs_10m_3_filt.mp4",
        name="Oceans_fs_10m_3",
    ),
]
