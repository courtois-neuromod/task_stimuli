from ..tasks import task_base, video

TASKS = []

for episode in list(range(1,24)):
    segments = "abcd" if episode in (23,) else ("abc" if episode in (16,) else "ab")
    for segment in segments:
        TASKS.append(
            video.SingleVideo(
                "data/videos/friends/s7/friends_s07e%02d%s.mkv" % (episode, segment),
                aspect_ratio=4 / 3.0,
                startend_fixduration=2.0,
                name="task-friends-s7e%d%s" % (episode, segment),
                use_eyetracking=True,
            )
        )
        TASKS.append(task_base.Pause(
            text="You can take a short break.",
        ))
