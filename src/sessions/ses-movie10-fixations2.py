from ..tasks import images, video, memory, task_base

TASKS = []

segments = [
    ('bourne', 7, 372 / 157),
    ('life', 4, 12 / 5),
    ('figures', 8, 12 / 5),
    ('wolf', 11, 12 / 5),
]

for movie, seg_idx, ar in segments:
    TASKS.append(
        video.SingleVideo(
            f"data/videos/movie10/{movie}/{movie}{seg_idx:02d}.mkv",
            aspect_ratio=ar,
            startend_fixduration=0.0,#2.0,
            inmovie_fixations=True,
            infix_freq=20,
            infix_dur=1.5,
            name=f"task-{movie}{seg_idx:02d}-fixations",
            use_eyetracking=True
        )
    )
