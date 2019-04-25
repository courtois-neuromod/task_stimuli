from ..tasks import images, video, memory, task_base

TASKS = []
for seg_idx in range(7,13):
    TASKS.append(
        video.SingleVideo(
            'data/videos/life1/life1_seg%02d.mkv'%seg_idx,
            aspect_ratio = 12/5,
            name='life1_seg-%d'%seg_idx))

# 410 volumes each, last run is 375 volumes long
