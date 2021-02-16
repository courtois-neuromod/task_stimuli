from ..tasks import video

TASKS = []

for episode in range(1, 23):
    for segment in "ab":
        TASKS.append(
            video.SingleVideo(
                "data/videos/friends/s5/friends_s05e%02d%s.mkv" % (episode, segment),
                aspect_ratio=4 / 3.0,
                name="task-friends-s5e%d%s" % (episode, segment),
            )
        )

for segment in 'abcd':
    TASKS.append(
        video.SingleVideo(
            'data/videos/friends/s5/friends_s05e%02d%s.mkv'%(23, segment),
            aspect_ratio = 4/3.,
            name='task-friends-s5e%d%s'%(23, segment)))

