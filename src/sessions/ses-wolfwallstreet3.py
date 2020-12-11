from ..tasks import images, video, memory, task_base

TASKS = []
for seg_idx in range(13, 18):
    TASKS.append(
        video.SingleVideo(
            "data/videos/the_wolf_of_wall_street/the_wolf_of_wall_street_seg%02d.mkv"
            % seg_idx,
            aspect_ratio=12 / 5,
            name="the_wolf_of_wall_street_seg-%d" % seg_idx,
        )
    )
