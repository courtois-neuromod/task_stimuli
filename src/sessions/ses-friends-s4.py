from ..tasks import video

TASKS = []

for episode in range(1, 23):
    for segment in "ab":
        TASKS.append(
            video.SingleVideo(
                "data/videos/friends/s4/friends_s4e%02d%s.mkv" % (episode, segment),
                aspect_ratio=4 / 3.0,
                name="task-friends-s4e%d%s" % (episode, segment),
            )
        )
"""
for segment in 'abcd':
    TASKS.append(
        video.SingleVideo(
            'data/videos/friends/s4/friends_s4e%02d%s.mkv'%(23, segment),
            aspect_ratio = 4/3.,
            name='task-friends-s4e%d%s'%(23, segment)))
"""
