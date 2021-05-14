from ..tasks import video, task_base
import numpy as np

"""
Emotions task, study replication of Horikawa & al. 2020
(https://openneuro.org/datasets/ds002425/versions/1.0.0)

Gifs under 8 seconds are repeated until they go over 8 secs

All stimulus blocks were followed by an additional 2-s rest period.
Additional 32- and 6-s rest periods were added to the beginning and
end of each run respectively

ISI should be TR period

stimuli are randomized in-between subjects (to avoid order of presentation eff)

Runs should be under 10 mins

HELP needed with :
- prompting fixation cross
- prompting the subject with valence and arousal (could be on
both sides of the controller, arrows for arousal and buttons for valence)

"""


def get_videos(subject, session):
    """
    Create list of stimuli.
    """
    video_idx = np.loadtxt(
        "data/cowengif/order_fmri_neuromod.csv", delimiter=",", skiprows=1,
        dtype=np.int
    )
    selected_idx = video_idx[video_idx[:, 0] == session, subject + 1]
    return selected_idx


def get_tasks(parsed):
    """
    Present list of stimuli.

    fixation cross should be added at the beggining and end of run.
    """

    tasks = []

    video_indices = get_videos(int(parsed.subject), int(parsed.session))

    for idx in video_indices:
        tasks.append(
            video.SingleVideo(
                f"data/cowengis/gifs/{idx:04d}.mp4",
                name=f"task-cowengif{idx:04d}"
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
