from ..tasks import task_base, video

TASKS = []

VIDEOS = ["chaplin", "mononoke", "passepartout", "planetearth", "pulpfiction", "wot"]
ASPECT_RATIOS = [4/3, 279/157, 4/3, 279/157, 279/157, 16/9]

for video, ar in zip(VIDEOS, ASPECT_RATIOS):
    for segment in range(1,3):
        TASKS.append(
            video.SingleVideo(
                f"data/videos/ood/{video}/task-{video}{segment}_video.mkv",
                aspect_ratio=ar,
                startend_fixduration=2.0,
                name=f"task-{video}{segment}",
                use_eyetracking=True,
            )
        )
        TASKS.append(task_base.Pause(
            text="You can take a short break.",
        ))
