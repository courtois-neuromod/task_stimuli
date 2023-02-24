from ..tasks import images, video, memory, task_base

TASKS = []

seg_idx = 7
TASKS.append(
    video.SingleVideo(
        "data/videos/bourne/bourne%02d.mkv" % seg_idx,
        aspect_ratio=372 / 157,
        startend_fixduration=0.0,#2.0,
        inmovie_fixations=True,
        infix_freq=20,
        infix_dur=1.5,
        name="bourne_seg-%d-fixations" % seg_idx,
        use_eyetracking=True
    )
)

seg_idx = 4
TASKS.append(
    video.SingleVideo(
        "data/videos/life/life%02d.mkv" % seg_idx,
        aspect_ratio=12 / 5,
        startend_fixduration=0.0,#2.0,
        inmovie_fixations=True,
        infix_freq=20,
        infix_dur=1.5,
        name="life_seg-%d-fixations" % seg_idx,
        use_eyetracking=True
    )
)

seg_idx = 8
TASKS.append(
    video.SingleVideo(
        "data/videos/figures/figures%02d.mkv" % seg_idx,
        aspect_ratio=12 / 5,
        startend_fixduration=0.0,#2.0,
        inmovie_fixations=True,
        infix_freq=20,
        infix_dur=1.5,
        name="figures_seg-%d-fixations" % seg_idx,
        use_eyetracking=True
    )
)

seg_idx = 11
TASKS.append(
    video.SingleVideo(
        "data/videos/wolf/wolf%02d.mkv" % seg_idx,
        aspect_ratio=12 / 5,
        startend_fixduration=0.0,#2.0,
        inmovie_fixations=True,
        infix_freq=20,
        infix_dur=1.5,
        name="wolf_seg-%d-fixations" % seg_idx,
        use_eyetracking=True
    )
)
