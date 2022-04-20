# Don't display 'Hello from the Pygame Community!'
from asyncio import subprocess
from os import environ
import sys
try:
    environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
except:
    pass

from ..tasks import robot, task_base
import logging
from cozmo_api.controller import Controller

NUC_ADDR = ("10.30.6.17", 6667)
COZMO_ADDR = ("172.31.1.1", 5551)
LOCAL_UDP_PORT = 5551
LOCAL_TCP_PORT = 6667
SERVER_TCP_PORT = 6667
NET = "labo"

from getpass import getpass
from subprocess import Popen, PIPE, call

def ssh_tunnel():
    """print("\n--CONFIGURING  SSH TUNNEL --")
    # the public key of the client must be configured on the server prior to the following (see https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-on-ubuntu-1804)

    # delete FIFO and kill listeners on port 6667
    print("cleaning up server...")
    command = 'ssh ' + NET + '@' + NUC_ADDR[0]  # ssh connection
    cleanProc = Popen(command, stdin=PIPE, stdout=PIPE, shell=True)
    command = str.encode('lsof -ti:6667 | xargs kill 9\n')  # kill listeners
    cleanProc.stdin.write(command)
    command = str.encode('cd /tmp/\n')  # cd to tmp dir
    cleanProc.stdin.write(command)
    command = str.encode('rm fifo\n')   # delete FIFO  
    cleanProc.stdin.write(command)
    command = str.encode('exit\n')  # exit ssh connection
    cleanProc.stdin.write(command)
    
    # open a TCP forward port with the SSH connection
    print("opening a TCP forward port with the SSH connection...")
    command = 'ssh -L ' + str(LOCAL_TCP_PORT) + ':localhost:' + str(SERVER_TCP_PORT) + ' ' + NET + '@' + NUC_ADDR[0] 
    sshProc = Popen(command, stdin=PIPE, stdout=PIPE, shell=True)
    
    # setup the TCP to UDP forward on the server
    print("setting up the TCP to UDP forward on the server...")
    sshProc.stdin.write(b"mkfifo /tmp/fifo\n")
    command = str.encode("nc -l -p 6667 < /tmp/fifo | nc -u " + COZMO_ADDR[0] +  " " + str(COZMO_ADDR[1]) + " > /tmp/fifo\n")
    sshProc.stdin.write(command)    
    
    # setup the UDP to TCP forward on the local machine
    print("setting up the UDP to TCP forward on the local machine...")
    localProc = Popen("mkfifo /tmp/fifo", stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    command = str.encode("nc -l -u -p " + str(LOCAL_UDP_PORT) + " < /tmp/fifo | nc localhost " + str(LOCAL_TCP_PORT) + " > /tmp/fifo\n")
    localProc.stdin.write(command)    

    print("-- ssh tunnel configured --\n")"""
    print("\n-- CONFIGURING  SSH TUNNEL --")
    print("opening a TCP forward port with the SSH connection and setting up the TCP to UDP forward on the server...")
    ssh_tunnel_tcp2udp_proc = Popen(['ssh', '-L', '6667:localhost:6667', 'labo@10.30.6.17', 
                                    'bash -c "mkfifo /tmp/fifo ; nc -l -p 6667 < /tmp/fifo | nc -u 172.31.1.1 5551 > /tmp/fifo"'], 
                                    stdin=PIPE, stderr=PIPE, stdout=PIPE)
    print("setting up the UDP to TCP forward on the local machine...")
    local_udp2tcp_proc = Popen(['bash', '-c', 'mkfifo /tmp/fifo ; nc -l -u -p 5551 < /tmp/fifo | nc localhost 6667 > /tmp/fifo'])
    print("-- ssh tunnel configured --\n")
    
def get_tasks(parsed):
    """ if parsed.test:
        mode = "test"
    else:
        mode = "default" 
    """

    ssh_tunnel()    

    mode = "default" 

    with Controller.make(
        mode=mode,
        robot_addr=NUC_ADDR,    #only in modified version of PyCozmo
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

