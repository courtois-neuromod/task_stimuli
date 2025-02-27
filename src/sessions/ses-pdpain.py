import os
import random
from ..tasks.narratives import AudioRecording
from ..tasks.task_base import Pause

def get_tasks(parsed):



    for i in range(1,4):


        yield AudioRecording(
            name=f"task-painexpectancy_run-{i:02d}",
            max_duration=716,
            use_eyetracking=True,
            et_calibrate=False,
            )
