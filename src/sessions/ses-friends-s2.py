from ..tasks import video

TASKS = []

for episode in range(1, 25):
    for segment in "ab":
        TASKS.append(
            video.SingleVideo(
                "data/videos/friends/s2/friends_s2e%02d%s.mkv" % (episode, segment),
                aspect_ratio=4 / 3.0,
                name="task-friends-s2e%d%s" % (episode, segment),
            )
        )
