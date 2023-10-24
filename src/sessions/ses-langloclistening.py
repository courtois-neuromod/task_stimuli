from ..tasks import language, task_base
import glob
from pathlib import Path
import numpy as np     

# C_LIST:  if run 1 uses list 1, run 2 should also use list 1.
C_LIST = 1

# C_ORDER: The localizer is meant to be run twice. 
# The C_ORDER is the counter-balance number, and should have the value 1
# or 2 delineating one of two possible stim orders. 
# 1: I D D I   D I D I   I D I D   D I I D
# 2: D I I D   I D I D   D I D I   I D D I
# It doesn't matter which order is used first, just that the subject sees both orders.
########## RIGHT NOW HARD-CODING ORDER 1 FOR RUN 1 AND ORDER 2 FOR RUN 2


def get_audios(C_ORDER, C_LIST):

    if C_ORDER==1:
        order = [1,2,2,1,2,1,2,1,1,2,1,2,2,1,1,2]
    elif C_ORDER==2:
        order = [2,1,1,2,1,2,1,2,2,1,2,1,1,2,2,1]

    if C_LIST==1:
        INT_LIST_dir = 'data/language/localizer/listening_list1/int/'
        tmp = [str(s) for s in Path(INT_LIST_dir).rglob('*wav')]
        INT_FILELIST = sorted(tmp, key=lambda x: int(x.split("/")[-1].split("_")[0]))
        DEGR_LIST_dir = 'data/language/localizer/listening_list1/degr/'
        tmp = [str(s) for s in Path(DEGR_LIST_dir).rglob('*wav')]
        DEGR_FILELIST = sorted(tmp, key=lambda x: int(x.split("/")[-1].split("_")[0]))
        
    elif C_LIST==2:
        INT_LIST_dir = 'data/language/localizer/listening_list2/int/'
        tmp = [str(s) for s in Path(INT_LIST_dir).rglob('*wav')]
        INT_FILELIST = sorted(tmp, key=lambda x: int(x.split("/")[-1].split("_")[0]))
        DEGR_LIST_dir = 'data/language/localizer/listening_list2/degr/'
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

TASKS = []
for run_N in range(1, 2):
    
    STIM_LIST = get_audios(run_N, C_LIST)
    for idx in np.arange(len(STIM_LIST)):
        TASKS.append(
            language.Listening(STIM_LIST[idx], wait_key=True, name="test"),
            )
        #continue
        TASKS.append(
            task_base.Pause(
                """This is a pause"""
                )
            )