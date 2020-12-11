from ..tasks import images, video, memory, task_base

TASKS = [
    task_base.Pause(
        """Hi! We are about to start the MRI session.
Make yourself comfortable.
Ensure that you can see the full screen and that the image is sharp.
Please keep your eyes open."""
    ),
    speech.Speech("data/speech/motion_study_speech_words.csv", name="Speech"),
    video.SingleVideo("data/videos/Inscapes-67962604.mp4", name="Inscapes"),
    # source: https://drive.google.com/file/d/1prOM1QuPEAcqe_D-3rLYNu937A8VzbsB/view
    video.SingleVideo("data/videos/tammy/Oceans_1.mp4", name="Oceans_chunk1"),
    videogame.VideoGame(
        state_name="Level1", name="ShinobiIIIReturnOfTheNinjaMaster-test"
    ),
]

# TODO: randomize the order of the tasks?
