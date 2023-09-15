from ..tasks import task_base, video

TASKS = []

for episode in list(range(1, 16))+list(range(17,25)):
    segments = "abcd" if episode in (15,24) else "ab"
    for segment in segments:
        TASKS.append(
            video.SingleVideo(
                "data/videos/friends/s6/friends_s06e%02d%s.mkv" % (episode, segment),
                aspect_ratio=4 / 3.0,
                startend_fixduration=2.0,
                name="task-friends-s6e%d%s" % (episode, segment),
                use_eyetracking=True,
            )
        )


