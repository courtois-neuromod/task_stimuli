# Don't display 'Hello from the Pygame Community!'
from os import environ

try:
    environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
except:
    pass

from ..tasks import robot_unified, task_base

def get_tasks(parsed):

    for run in range(2):
        task = robot_unified.CozmoFirstTaskPsychoPyNUC(
            nuc_addr="10.30.6.17",
            tcp_port_send=1025,
            tcp_port_recv=1024,
            max_duration=4,
            name=f"cozmo_run-{run+1:02d}",
            instruction="Explore the maze and find the target !",
        )
        yield task

        if task._task_completed:
            print("Task completed.")

        yield task_base.Pause(
                text="You can take a short break while we reset Cozmo.",
            )