

from ..tasks.narratives import Story, FreeRecall, RecencyJudgments

TASKS = [
    RecencyJudgments(
        design_file='data/narratives.stimuli/recency_segments/lucy/first_viewing_lucy.csv',
        name="task-lucyrecency_run-01"),
    FreeRecall(name="task-lucyrecall_run-01", max_duration=30),
    Story(
        sound_file='./data/narratives.stimuli/audio_files/test.wav',
        name="task-lucy_run-01"),

]
