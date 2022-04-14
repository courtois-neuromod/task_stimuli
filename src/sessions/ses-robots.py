# Don't display 'Hello from the Pygame Community!'
from os import environ
try:
    environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
except:
    pass

from ..tasks import robot, task_base
import logging
from cozmo_api.controller import Controller

NUC_ADDR = None
#TODO:
"""
NUC_ADDR = ("10.30.6.17", 6667)
COZMO_ADDR = ("172.31.1.1", 5551)
LOCAL_UDP_PORT = 53
LOCAL_TCP_PORT = 6667
SERVER_TCP_PORT = 6667
NET = "labo"

from getpass import getpass
from subprocess import Popen, PIPE

# get sudo passsword
password = getpass("Please enter server's password: ")
# open a TCP forward port with the SSH connection
proc = Popen("ssh -L " + str(LOCAL_TCP_PORT) + ":localhost:" + str(SERVER_TCP_PORT) + " " + NET + "@" + NUC_ADDR[0], stdin=PIPE)
proc.communicate(password.encode())
# setup the TCP to UDP forward on the server
proc = Popen("mkfifo /tmp/fifo")
proc = Popen("nc -l -p 6667 < /tmp/fifo | nc -u " + COZMO_ADDR[0] +  " " + str(COZMO_ADDR[1]) + " > /tmp/fifo")
# setup the UDP to TCP forward on the local machine
os.system("mkfifo /tmp/fifo")
os.system("sudo nc -l -u -p " + str(LOCAL_UDP_PORT) + " < /tmp/fifo | nc localhost " + str(LOCAL_TCP_PORT) + " > /tmp/fifo")    #TODO: able to run commands after that ?
"""

def get_tasks(parsed):
    """ if parsed.test:
        mode = "test"
    else:
        mode = "default" 
    """

    mode = "default" 

    with Controller.make(
        mode=mode,
        robot_addr=NUC_ADDR,
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

