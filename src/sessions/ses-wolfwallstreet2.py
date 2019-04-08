from ..tasks import images, video, memory, task_base

TASKS = [

    video.SingleVideo(
        'data/videos/subject_setup_videos/sub-default_setup_video.mp4', name='Inscapes'),

    task_base.Pause(),
]
for seg_idx in range(6,13):
    TASKS.append(
        video.SingleVideo(
            'data/videos/the_wolf_of_wall_street/the_wolf_of_wall_street_seg%02d.mkv'%seg_idx,
            aspect_ratio = 12/5,
            name='bourne_supremacy_seg-%d'%seg_idx))
