import os

from ..tasks.narratives import Story, FreeRecall, RecencyJudgments

STORIES = [ 'black','forgot','lucy','notthefallintact','pieman','prettymouth','slumlordreach','tunnel']
STORIES_DURATIONS = [ 800,837,542,581,450,712,1801,1533]

STIMULI_PATH  = 'data/narratives.stimuli'

def get_tasks(parsed):

    for story, story_duration in zip(STORIES, STORIES_DURATIONS):
        story_cap = story.capitalize()
        yield Story(
            sound_file=os.path.join(STIMULI_PATH, 'audio_files', f"{story}_audio.wav"),
            name=f"task-{story_cap}Story_run-01")
        yield FreeRecall(name="task-{story_cap}Recall_run-01", max_duration=story_duration*.4)
        yield RecencyJudgments(
                design_file=os.path.join(STIMULI_PATH, 'recency_segments', story, f"first_viewing_{story}.csv"),
                name="task-{story_cap}Recency_run-01")
