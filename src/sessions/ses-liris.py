from ..tasks import video, task_base
import numpy as np


def get_videos(subject, session):
    video_idx = np.loadtxt(
        "data/liris/order_fmri_neuromod.csv", delimiter=",", skiprows=1, dtype=np.int
    )
    selected_idx = video_idx[video_idx[:, 0] == session, subject + 1]
    return selected_idx


def get_tasks(parsed):

    tasks = []

    video_indices = get_videos(int(parsed.subject), int(parsed.session))

    for idx in video_indices:
        tasks.append(
            video.SingleVideo(
                f"data/liris/videos/{idx:03d}.mp4", name=f"task-liris{idx:03d}"
            )
        )
        continue
        tasks.append(
            task_base.Pause(
                """The video is finished.
The scanner might run for a few seconds to acquire more images.
Please remain still."""
            )
        )
    return tasks
