from ..tasks import language, task_base
import glob
from pathlib import Path
import numpy as np     

# The localizer is meant to be run twice. 
# where should this be (or come from)?
C_ORDER = 1
C_RUN = 1

def get_audios(C_ORDER, C_RUN):

    if C_ORDER==1:
        order = [1,2,2,1,2,1,2,1,1,2,1,2,2,1,1,2]
    elif C_ORDER==2:
        order = [2,1,1,2,1,2,1,2,2,1,2,1,1,2,2,1]

    if C_RUN==1:
        INT_LIST_dir = 'data/language/localizer/audio_list1/int/'
        tmp = [str(s) for s in Path(INT_LIST_dir).rglob('*wav')]
        INT_FILELIST = sorted(tmp, key=lambda x: int(x.split("/")[-1].split("_")[0]))
        DEGR_LIST_dir = 'data/language/localizer/audio_list1/degr/'
        tmp = [str(s) for s in Path(DEGR_LIST_dir).rglob('*wav')]
        DEGR_FILELIST = sorted(tmp, key=lambda x: int(x.split("/")[-1].split("_")[0]))
        
    elif C_RUN==2:
        INT_LIST_dir = 'data/language/localizer/audio_list2/int/'
        tmp = [str(s) for s in Path(INT_LIST_dir).rglob('*wav')]
        INT_FILELIST = sorted(tmp, key=lambda x: int(x.split("/")[-1].split("_")[0]))
        DEGR_LIST_dir = 'data/language/localizer/audio_list2/degr/'
        tmp = [str(s) for s in Path(DEGR_LIST_dir).rglob('*wav')]
        DEGR_FILELIST = sorted(tmp, key=lambda x: int(x.split("/")[-1].split("_")[0]))
    int_idx = 1
    degr_idx = 1
    STIM_LIST = []
    for stim_idx in np.arange(0,16):
        # get real speech
        if order[stim_idx] == 1:
            STIM_LIST.append(INT_FILELIST[int_idx])
            int_idx = int_idx+1
        # get distorted
        elif order[stim_idx] == 2:
            STIM_LIST.append(DEGR_FILELIST[degr_idx])
            degr_idx = degr_idx+1   
    return STIM_LIST

def get_tasks(parsed):
    tasks = []
    STIM_LIST = get_audios(C_ORDER, C_RUN)
    STIM_LIST = STIM_LIST[:3]
    for idx in np.arange(len(STIM_LIST)):
        tasks.append(
            language.Listening(STIM_LIST[idx], wait_key=True, name="test"),
            # f"data/liris/videos/{idx:03d}.mp4", name=f"task-liris{idx:03d}"
        )
        continue
        tasks.append(
            task_base.Pause(
                """The audio is finished"""
            )
        )
    return tasks