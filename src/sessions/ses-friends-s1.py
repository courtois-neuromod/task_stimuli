from ..tasks import video

TASKS = []

for episode in range(1,25):
    for segment in range(1,3):
        TASKS.append(
            video.SingleVideo(
                'data/videos/friends/s1/friends_s1e%02d_seg-%02d.mkv'%(episode, segment),
                aspect_ratio = 4/3.,
                name='task-friends-s1e%d-seg%d'%(episode, segment)))
