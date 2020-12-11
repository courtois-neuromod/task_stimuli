from ..tasks import images, video, memory, task_base

TASKS = [
    video.SingleVideo(
        "data/videos/movies_for_montreal/03_Inscaped_NoScannerSound_h264.mov",
        name="Inscapes",
    ),
    video.SingleVideo("data/videos/tammy/Oceans_1.mp4", name="Oceans_chunk1"),
]
