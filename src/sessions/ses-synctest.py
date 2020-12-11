from ..tasks import video

TASKS = [
    video.SingleVideo("data/videos/Sync-Footage-V1-H264.mp4", name="task-synctest")
] * 10
