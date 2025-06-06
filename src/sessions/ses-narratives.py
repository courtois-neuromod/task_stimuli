import os
import random
from ..tasks.narratives import Story, FreeRecall, RecencyJudgments, AudioRecording, SoundTaskBase
from ..tasks.task_base import Pause
from subprocess import Popen, DEVNULL

STORIES_BLOCK1 = [['lucy', 'forgot'], ['black', 'notthefall']]
STORIES_DURATIONS_BLOCK1 = [[542.12, 837], [800, 581.84]]
STORIES_BLOCK2 = [['slumlord', 'pieman'],['prettymouth', 'tunnel_part1', 'tunnel_part2']]
STORIES_DURATIONS_BLOCK2 = [[929.5, 450],[712, 747.76, 786.01]]

STORIES = sum(STORIES_BLOCK1 + STORIES_BLOCK2, [])
STORIES_DURATIONS = sum(STORIES_DURATIONS_BLOCK1 + STORIES_DURATIONS_BLOCK2, [])

STIMULI_PATH  = 'data/narratives.stimuli'

pause_message = "You can take a short break while we stop the scanner.\n\n When the scanner is stopped you can press A when ready to continue"

def get_tasks(parsed):


    if int(parsed.session) <= 6:
        if int(parsed.session)%2==1:
            stories = list(zip(STORIES_BLOCK1[0], STORIES_DURATIONS_BLOCK1[0]))
        else:
            stories = list(zip(STORIES_BLOCK1[1], STORIES_DURATIONS_BLOCK1[1]))
    else:
        if int(parsed.session)%2==1:
            stories = list(zip(STORIES_BLOCK2[0], STORIES_DURATIONS_BLOCK2[0]))
        else:
            stories = list(zip(STORIES_BLOCK2[1], STORIES_DURATIONS_BLOCK2[1]))
        
    #stories = list(zip(STORIES, STORIES_DURATIONS))
    #stories = random.sample(stories, len(stories))

    first_story = True
    for story, story_duration in stories:
        story_cap = story.capitalize()

        yield Story(
            sound_file=os.path.join(STIMULI_PATH, 'audio_files_filtered', f"{story}_audio.wav"),
            name=f"task-{story_cap}Story_run-01",
            use_eyetracking=True,
            et_calibrate=first_story,
            )

        first_story = False
        yield Pause(
            text=pause_message,
            wait_key='a',
        )

        yield FreeRecall(
            name=f"task-{story_cap}Recall_run-01",
            max_duration=story_duration,
            use_eyetracking=True,
            et_calibrate=False,
            )

        yield Pause(
            text=pause_message,
            wait_key='a',
        )
        if not 'part1' in story:
            story_full = story.replace('_part2','')
            yield RecencyJudgments(
                    design_file=os.path.join(STIMULI_PATH, 'recency_segments', story_full, f"first_viewing_{story_full}.csv"),
                    use_eyetracking=True,
                    name=f"task-{story_full.capitalize()}Recency_run-01",)

            yield Pause(
                text=pause_message,
                wait_key='a',
            )
