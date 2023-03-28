import os
import random
from ..tasks.narratives import Story, FreeRecall, RecencyJudgments
from ..tasks.task_base import Pause

STORIES = [ 'black','forgot','lucy','notthefallintact','pieman','prettymouth','slumlordreach','tunnel']
STORIES_DURATIONS = [ 800,837,542,581,450,712,1801,1533]

STIMULI_PATH  = 'data/narratives.stimuli'

def get_tasks(parsed):

    stories = list(zip(STORIES, STORIES_DURATIONS))
    stories = random.sample(stories, len(stories))
    for story, story_duration in stories:
        story_cap = story.capitalize()

        yield Story(
            sound_file=os.path.join(STIMULI_PATH, 'audio_files', f"{story}_audio.wav"),
            name=f"task-{story_cap}Story_run-01")

        yield Pause(
            text="You can take a short break while we stop the scanner.\n Then press A when ready to continue",
            wait_key='a',
        )

        yield FreeRecall(name=f"task-{story_cap}Recall_run-01", max_duration=story_duration*.4)

        yield Pause(
            text="You can take a short break while we stop the scanner.\n Then press A when ready to continue",
            wait_key='a',
        )

        yield RecencyJudgments(
                design_file=os.path.join(STIMULI_PATH, 'recency_segments', story, f"first_viewing_{story}.csv"),
                name=f"task-{story_cap}Recency_run-01")

        yield Pause(
            text="You can take a short break while we stop the scanner.\n Then press A when ready to continue",
            wait_key='a',
        )
