import os
from ..tasks import language, task_base

STIMULI_PATH = 'data/language/localizer'

TASKS = [
    language.ReadingBlocks(
        os.path.join(STIMULI_PATH, 'designs/reading_dummy.tsv'),
        name='task-locreading_run-01'),
    language.ListeningBlocks(
        os.path.join(STIMULI_PATH, 'designs/auditory_1.tsv'),
        os.path.join(STIMULI_PATH, 'funloc_norm_clips'),
        name='task-locauditory_run-01')
]
