# Don't display 'Hello from the Pygame Community!'
from os import environ

try:
    environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
except:
    pass

from ..tasks import robot, task_base


def get_tasks(parsed):
    n_tasks = 2
    for run in range(n_tasks):
        task = robot.CozmoFirstTaskPsychoPyNUC(
            nuc_addr="10.30.6.17",
            tcp_port_send=1025,
            tcp_port_recv=1024,
            max_duration=15,
            name=f"cozmo_run-{run+1:02d}",
            instruction="Explore the maze and find the target !",
        )
        yield task

        if task._task_completed:
            print("Task completed.")

        if run < n_tasks - 1:
            yield task_base.Pause(
                text="You can take a short break while we reset Cozmo.",
            )
