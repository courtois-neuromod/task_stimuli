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
        "data/videos/Oceans_fs_10m_filt/Oceans_fs_10m_7_filt.mp4",
        name="Oceans_fs_10m_7",
    ),
    video.SingleVideo(
        "data/videos/Oceans_fs_10m_filt/Oceans_fs_10m_8_filt.mp4",
        name="Oceans_fs_10m_8",
    ),
    video.SingleVideo(
        "data/videos/Oceans_fs_10m_filt/Oceans_fs_10m_9_filt.mp4",
        name="Oceans_fs_10m_9",
    ),
    video.SingleVideo(
        "data/videos/Oceans_fs_10m_filt/Oceans_fs_10m_10_filt.mp4",
        name="Oceans_fs_10m_10",
    ),
]
