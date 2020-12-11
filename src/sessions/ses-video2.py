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
        "data/videos/Oceans_fs_10m_filt/Oceans_fs_10m_4_filt.mp4",
        name="Oceans_fs_10m_4",
    ),
    video.SingleVideo(
        "data/videos/Oceans_fs_10m_filt/Oceans_fs_10m_5_filt.mp4",
        name="Oceans_fs_10m_5",
    ),
    video.SingleVideo(
        "data/videos/Oceans_fs_10m_filt/Oceans_fs_10m_6_filt.mp4",
        name="Oceans_fs_10m_6",
    ),
    video.SingleVideo(
        "data/videos/Oceans_fs_10m_filt/Oceans_fs_10m_7_filt.mp4",
        name="Oceans_fs_10m_7",
    ),
]
