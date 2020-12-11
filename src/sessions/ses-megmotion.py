from ..tasks import images, video, memory, task_base

TASKS = [
    task_base.Fixation(duration=7 * 60, name="resting_state"),
    task_base.Pause(),
    video.SingleVideo(
        "data/videos/movies_for_montreal/03_Inscaped_NoScannerSound_h264.mov",
        name="Inscapes",
    ),
    task_base.Pause(),
    video.SingleVideo(
        "data/videos/movies_for_montreal/Oceans_10m_fs.mp4", name="Oceans"
    ),
    task_base.Pause(),
    task_base.Fixation(duration=7 * 60, name="resting_state"),
    task_base.Pause(),
    video.SingleVideo(
        "data/videos/movies_for_montreal/03_Inscaped_NoScannerSound_h264.mov",
        scaling=0.5,
        name="Inscapes_scaled",
    ),
    task_base.Pause(),
    video.SingleVideo(
        "data/videos/movies_for_montreal/Oceans_10m_fs.mp4",
        scaling=0.5,
        name="Oceans_scaled",
    ),
]
