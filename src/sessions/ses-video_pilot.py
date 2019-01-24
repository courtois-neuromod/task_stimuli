from ..tasks import images, video, memory, task_base

TASKS = [
    task_base.Pause("""Hi! We are about to start the MRI session.
Make yourself comfortable.
Ensure that you can see the full screen and that the image is sharp.
Today you are going to watch videos.
Please keep your eyes opened."""),
    video.SingleVideo(
        'data/videos/Inscapes-67962604.mp4', name='Inscapes'),
    task_base.Pause(),
    video.SingleVideo(
        'data/videos/tammy/Oceans_1.mp4',
        name='Oceans_chunk1'),
    ]
