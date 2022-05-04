# Don't display 'Hello from the Pygame Community!'
from asyncio import subprocess
from os import environ
import sys
try:
    environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
except:
    pass

from ..tasks import robot_nuc
import logging
    
def get_tasks(parsed):

    for run in range(3):
        task = robot_nuc.CozmoFirstTaskPsychoPyNUC(
            max_duration=15,
            name=f"cozmo_run-{run+1:02d}",
            instruction="Explore the maze and find the target !",
        )
        yield task

        if task._task_completed:
            print("Task completed.")
            
            

