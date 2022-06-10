# Don't display 'Hello from the Pygame Community!'
from asyncio import subprocess
from os import environ

try:
    environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
except:
    pass

from ..tasks import robot_unified, task_base
import logging
from cozmo_api.controller import Controller

NUC_ADDR = ("10.30.6.17", 6667)
COZMO_ADDR = ("172.31.1.1", 5551)
LOCAL_UDP_PORT = 5551
LOCAL_TCP_PORT = 6667
SERVER_TCP_PORT = 6667
NET = "labo"

from subprocess import Popen, PIPE

def ssh_tunnel():
    # the public key of the client must be configured on the server prior to the following (see https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-on-ubuntu-1804)
    print("\n-- CONFIGURING SSH TUNNEL --")
    print("opening a TCP forward port with the SSH connection and setting up the TCP to UDP forward on the server...")
    ssh_tunnel_tcp2udp_proc = Popen(['ssh', '-L', f'{LOCAL_TCP_PORT}:localhost:{SERVER_TCP_PORT}', f'{NET}@{NUC_ADDR[0]}', 
                                    f'bash -c "mkfifo /tmp/fifo ; nc -l -p {SERVER_TCP_PORT} < /tmp/fifo | nc -u {COZMO_ADDR[0]} {COZMO_ADDR[1]} > /tmp/fifo"'], 
                                    stdin=PIPE, stderr=PIPE, stdout=PIPE)
    print("setting up the UDP to TCP forward on the local machine...")
    local_udp2tcp_proc = Popen(['bash', '-c', f'mkfifo /tmp/fifo ; nc -l -u -p {LOCAL_UDP_PORT} < /tmp/fifo | nc localhost {LOCAL_TCP_PORT} > /tmp/fifo'])
    print("-- ssh tunnel configured --\n")
    
def get_tasks(parsed):
   
    #ssh_tunnel()    

    with Controller.make(
        test=False,
        #robot_addr=('127.0.0.1', 5551),    #only in modified version of PyCozmo
        enable_procedural_face=False,
        log_level=logging.INFO,
        protocol_log_level=logging.INFO,
        robot_log_level=logging.INFO,
    ) as ctrlr:
        for run in range(3):
            task = robot_unified.CozmoFirstTaskPsychoPy(
                controller=ctrlr,
                max_duration=5,
                name=f"cozmo_run-{run+1:02d}",
                instruction="Explore the maze and find the target !",
            )
            yield task

            if task._task_completed:
                print("Task completed.")
            
            yield task_base.Pause(
                text="You can take a short break while we reset Cozmo.",
            )

