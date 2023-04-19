import os
import random
from ..tasks.narratives import Story, FreeRecall, RecencyJudgments
from ..tasks.task_base import Pause

STORIES_BLOCK1 = [['lucy', 'forgot'], ['black', 'notthefallintact']]
STORIES_DURATIONS_BLOCK1 = [[542.12, 837], [800, 581.84]]
STORIES_BLOCK2 = [['slurmlord', 'pieman'],['prettymouth', 'tunnel_part1', 'tunnel_part2']]
STORIES_DURATIONS_BLOCK2 = [[929.5, 450],[712, 747.76, 786.01]]

STORIES = sum(STORIES_BLOCK1 + STORIES_BLOCK2, [])
STORIES_DURATIONS = sum(STORIES_DURATIONS_BLOCK1 + STORIES_DURATIONS_BLOCK2, [])

STIMULI_PATH  = 'data/narratives.stimuli'

def get_tasks(parsed):

    stories = list(zip(STORIES, STORIES_DURATIONS))
    #stories = random.sample(stories, len(stories))
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
        if not 'part1' in story:
            story_full = story.replace('_part2','')
            yield RecencyJudgments(
                    design_file=os.path.join(STIMULI_PATH, 'recency_segments', story_full, f"first_viewing_{story_full}.csv"),
                    name=f"task-{story_full.capitalize()}Recency_run-01")

            yield Pause(
                text="You can take a short break while we stop the scanner.\n Then press A when ready to continue",
                wait_key='a',
            )
