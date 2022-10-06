from ..tasks import images, video, memory, task_base

TASKS = []

seg_idx = 7
TASKS.append(
    video.SingleVideo(
        "data/videos/bourne_supremacy/bourne_supremacy_seg%02d.mkv" % seg_idx,
        aspect_ratio=372 / 157,
        startend_fixduration=0.0,#2.0,
        inmovie_fixations=True,
        infix_freq=20,
        infix_dur=1.5,
        name="bourne_supremacy_seg-%d-fixations" % seg_idx,
    )
)

seg_idx = 5
TASKS.append(
    video.SingleVideo(
        "data/videos/life1/life1_seg%02d.mkv" % seg_idx,
        aspect_ratio=12 / 5,
        startend_fixduration=0.0,#2.0,
        inmovie_fixations=True,
        infix_freq=20,
        infix_dur=1.5,
        name="life1_seg-%d-fixations" % seg_idx,
    )
)

seg_idx = 8
TASKS.append(
    video.SingleVideo(
        "data/videos/hidden_figures/hidden_figures_seg%02d.mkv" % seg_idx,
        aspect_ratio=12 / 5,
        startend_fixduration=0.0,#2.0,
        inmovie_fixations=True,
        infix_freq=20,
        infix_dur=1.5,
        name="hidden_figures_seg-%d-fixations" % seg_idx,
    )
)

seg_idx = 11
TASKS.append(
    video.SingleVideo(
        "data/videos/the_wolf_of_wall_street/the_wolf_of_wall_street_seg%02d.mkv" % seg_idx,
        aspect_ratio=12 / 5,
        startend_fixduration=0.0,#2.0,
        inmovie_fixations=True,
        infix_freq=20,
        infix_dur=1.5,
        name="the_wolf_of_wall_street_seg-%d-fixations" % seg_idx,
    )
)
