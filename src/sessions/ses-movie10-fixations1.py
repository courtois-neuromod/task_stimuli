from ..tasks import images, video, memory, task_base

TASKS = []


segments = [
    ('bourne', 6, 372 / 157),
    ('life', 3, 12 / 5),
    ('figures', 7, 12 / 5),
    ('wolf', 10, 12 / 5),
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
