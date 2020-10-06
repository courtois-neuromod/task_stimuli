from ..tasks import video, task_base
import numpy as np

NUM_VID_PRISME = 10

def get_videos(subject, session):
    video_idx = np.loadtxt(
        'data/emotions/order_fmri_neuromod.csv',
        delimiter=',',
        skiprows=1,
        dtype=np.int
    )
    selected_idx = video_idx[video_idx[:,0]==session, subject+1]
    print(selected_idx)
    return ["data/emotions/videos/%03d.mp4"%i for i in selected_idx]

def get_tasks(parsed):

    tasks = []

    video_paths = get_videos(int(parsed.subject), int(parsed.session))

    for p in video_paths:
        tasks.append(
            video.SingleVideo(
                p,
                name='emotion_%s'%video
            )
        )
        tasks.append(
            task_base.Pause(
            """The video is finished.
The scanner might run for a few seconds to acquire more images.
Please remain still."""
            )
        )
    return tasks
