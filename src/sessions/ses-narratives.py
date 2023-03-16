from ..tasks.narratives import Story, FreeRecall

TASKS = [
    FreeRecall(device='', name="task-lucyrecall_run-01"),
    Story(
        sound_file='./data/narratives.stimuli/audio_files/test.wav',
        name="task-lucy_run-01"),
]
