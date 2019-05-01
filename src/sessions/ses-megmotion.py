from ..tasks import images, video, memory, task_base

TASKS = [
    task_base.Fixation(duration=7*60, name='resting_state'),
    video.SingleVideo(
        'data/videos/movies_for_montreal/03_Inscaped_NoScannerSound_h264.mov',
        name='Inscapes'),
    video.SingleVideo(
        'data/videos/movies_for_montreal/Oceans_10m_fs.mp4',
        name='Oceans_fs_10m_2')
]
