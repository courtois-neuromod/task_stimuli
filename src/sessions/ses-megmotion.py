from ..tasks import images, video, memory, task_base, eye_movements

TASKS = [

    eye_movements.EyetrackerTask(name='eye_mvts'),
    task_base.Pause(),
    task_base.Fixation(duration=7*60, name='resting_state'),
    task_base.Pause(),
    video.SingleVideo(
        'data/videos/movies_for_montreal/03_Inscaped_NoScannerSound_h264.mov',
        name='Inscapes_1'),
    task_base.Pause(),
    video.SingleVideo(
        'data/videos/movies_for_montreal/Oceans_10m_fs.mp4',
        name='Oceans_1'),
    task_base.Pause(),
    task_base.Fixation(duration=7*60, name='resting_state'),
    task_base.Pause(),
    video.SingleVideo(
        'data/videos/movies_for_montreal/03_Inscaped_NoScannerSound_h264.mov',
        name='Inscapes_2'),
    task_base.Pause(),
    video.SingleVideo(
        'data/videos/movies_for_montreal/Oceans_10m_fs.mp4',
        name='Oceans_2')
]
