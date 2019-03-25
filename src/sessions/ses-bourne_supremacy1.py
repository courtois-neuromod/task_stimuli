from ..tasks import images, video, memory, task_base

TASKS = [

    video.SingleVideo(
        'data/videos/bourne_test.mkv',
        name='bourne_supremacy_test'),

    video.SingleVideo(
        'data/videos/subject_setup_videos/sub-default_setup_video.mp4', name='Inscapes'),

    task_base.Pause(),

    video.SingleVideo(
        'data/videos/bourne_supremacy/bourne_supremacy_seg01.mkv',
        name='bourne_supremacy_1'),

    video.SingleVideo(
        'data/videos/bourne_supremacy/bourne_supremacy_seg10.mkv',
        name='bourne_supremacy_10'),

]
