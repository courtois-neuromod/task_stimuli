from ..tasks import video

TASKS = []

# de-comment line 7 when done piloting
#for episode in list(range(1, 4)): # to test, just not to download the entire season for local tests
for episode in list(range(1, 16))+list(range(17,25)):
    segments = "abcd" if episode in (15,24) else "ab"
    for segment in segments:
        TASKS.append(
            video.SingleVideo(
                "data/videos/friends/s6/friends_s06e%02d%s.mkv" % (episode, segment),
                aspect_ratio=4 / 3.0,
                startend_fixduration=0.0,#2.0,
                inmovie_fixations=True,
                infix_freq=20,
                infix_dur=1.5,
                name="task-friends-s6e%d%s-fixations" % (episode, segment),
                use_eyetracking=True,
            )
        )
