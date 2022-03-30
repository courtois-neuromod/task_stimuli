from ..tasks import video

TASKS = []

for episode in range(1, 23):
    segments = "abcd" if episode in [23] else "ab"
    for segment in segments:
        TASKS.append(
            video.SingleVideo(
                "data/videos/friends/s5/friends_s05e%02d%s.mkv" % (episode, segment),
                aspect_ratio=4 / 3.0,
                name="task-friends-s5e%d%s" % (episode, segment),
                use_eyetracking=True,
            )
        )

    

