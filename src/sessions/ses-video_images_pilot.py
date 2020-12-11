from ..tasks import images, video, memory, task_base

TASKS = [
    # memory.ImagePosition('data/memory/stimuli.csv', use_fmri=parsed.fmri, use_eyetracking=True),
    video.SingleVideo(
        "data/videos/Inscapes-67962604.mp4",
        name="Inscapes",
        use_fmri=parsed.fmri,
        use_eyetracking=True,
    ),
    task_base.Pause(),
    video.SingleVideo(
        "data/videos/skateboard_fails.mp4",
        name="skateboard_fails",
        use_fmri=parsed.fmri,
        use_eyetracking=True,
    ),
    images.Images(
        "data/images/test_conditions.csv",
        "/home/basile/data/projects/task_stimuli/data/images/bold5000/Scene_Stimuli/Presented_Stimuli/ImageNet",
        name="bold5000",
        use_fmri=parsed.fmri,
        use_eyetracking=True,
    ),
]
