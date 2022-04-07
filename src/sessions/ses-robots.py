# Don't display 'Hello from the Pygame Community!'
from os import environ
try:
    environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
except:
    pass

from ..tasks import robot, task_base
import logging
from cozmo_api.controller import Controller

def get_tasks(parsed):
    """ if parsed.test:
        mode = "test"
    else:
        mode = "default" 
    """

    mode = "default" 

    with Controller.make(
        mode=mode,
        enable_procedural_face=False,
        log_level=logging.INFO,
        protocol_log_level=logging.INFO,
        robot_log_level=logging.INFO,
    ) as ctrlr:
        for run in range(3):
            task = robot.CozmoFirstTaskPsychoPy(
                controller=ctrlr,
                max_duration=15,
                name=f"cozmo_run-{run+1:02d}",
                instruction="Explore the maze and find the target !",
            )
            yield task

            if task._task_completed:
                print("Task completed.")
            
            """yield task_base.Pause(
                text="You can take a short break while we reset Cozmo.",
            )"""

