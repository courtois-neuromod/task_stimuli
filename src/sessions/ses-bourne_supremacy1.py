from ..tasks import images, video, memory, task_base

TASKS = []
for seg_idx in range(1, 6):
    TASKS.append(
        video.SingleVideo(
            "data/videos/movie10/bourne/bourne%02d.mkv" % seg_idx,
            aspect_ratio=372 / 157,
            name="bourne_supremacy_seg-%d" % seg_idx,
        )
    )
