from ..tasks import language, task_base
import glob
from pathlib import Path
import numpy as np     

# Trial blocks: 12 (18 seconds each)
# Fixation blocks: 3 (12 seconds each)
# Total runtime: 252 seconds (4:12)
# IPS for TR=2: 126

mainLanguage = 'English'  # or 'French'
# The primary language you want to test. This language will be
#  presented in both 'intact' and 'degraded' versions.

foreignLangauge = 'Tamil' 
# Langauge you want to use for the foreign condition.

C_LIST = 1
# specifies the subset of materials to use
# must be the same across runs for a subject
# list 1, use odd intact materials and even degraded materials
# list 2, use even intact materials and odd degraded materials

C_RUN = 1
# 1, 2, or 3 

C_ORDER = 1
#  conditionOrder (1, 2, or 3)
#  Specifies the condition block ordering.
# The conditions are
#       'X'  Fixation
#       'I'  Intact
#       'D'  Degraded
#       'F'  Foreign
# 1 = X I D F F D I X I D F F D I X
# 2 = X D F I I F D X D F I I F D X
# 3 = X F I D D I F X F I D D I F X
# It doesn't matter which order is used first, just that the subject sees both orders.
########## RIGHT NOW HARD-CODING ORDER 1 FOR RUN 1, ORDER 2 FOR RUN 2, AND ORDER 3 FOR RUN 3

root = '/Users/valentinaborghesani/Documents/4_Projects/CNeuromod/All_Tasks/task_stimuli/data/language/localizer/alice/'

# get all INTACT
odd_INT_FILELIST = []
even_INT_FILELIST = []
I_LIST_dir = root + mainLanguage + '/intact/'
tmp = [str(s) for s in Path(I_LIST_dir).rglob('*wav')]
INT_FILELIST = sorted(tmp, key=lambda x: int(x.split("/")[-1].split("_")[0]))
for i in np.arange(len(INT_FILELIST)):
    if int(INT_FILELIST[i].split("/")[-1].split("_")[0]) % 2 == 0:
        even_INT_FILELIST.append(INT_FILELIST[i])
    else:
        odd_INT_FILELIST.append(INT_FILELIST[i])

# get all DEGRADED
odd_D_FILELIST = []
even_D_FILELIST = []
D_LIST_dir  = root + mainLanguage + '/degraded/'
tmp = [str(s) for s in Path(D_LIST_dir).rglob('*wav')]
D_FILELIST = sorted(tmp, key=lambda x: int(x.split("/")[-1].split("_")[0]))
for i in np.arange(len(D_FILELIST)):
    if int(D_FILELIST[i].split("/")[-1].split("_")[0]) % 2 == 0:
        even_D_FILELIST.append(D_FILELIST[i])
    else:
        odd_D_FILELIST.append(D_FILELIST[i])

# get all FOREIGN
odd_F_FILELIST = []
even_F_FILELIST = []
F_LIST_dir  = root + foreignLangauge + '/intact/'
tmp = [str(s) for s in Path(F_LIST_dir).rglob('*wav')]
F_FILELIST = sorted(tmp, key=lambda x: int(x.split("/")[-1].split("_")[0]))
for i in np.arange(len(F_FILELIST)):
    if int(F_FILELIST[i].split("/")[-1].split("_")[0]) % 2 == 0:
        even_F_FILELIST.append(F_FILELIST[i])
    else:
        odd_F_FILELIST.append(F_FILELIST[i])


def get_audios_alice(C_LIST):
    
    order = ["X","I",'D','F','F','D',"I","X", "I",'D','F','F','D',"I","X",
                 'X', 'D', 'F', 'I', 'I', 'F','D', 'X', 'D', 'F', 'I', 'I', 'F', 'D', 'X',
                 'X', 'F','I', 'D', 'D', 'I', 'F','X', 'F', 'I', 'D','D', 'I', 'F','X']
    
    STIM_LIST = []
    c_o_i = 0 
    c_o_d = 0 
    c_e_i = 0 
    c_e_d = 0 
    c_o_f = 0 
    c_e_f = 0 
    
    for trial, cond in enumerate(order):

        if cond == 'X':
            STIM_LIST.append('X')

        if cond == 'I':
            if C_LIST == 1:
                STIM_LIST.append(odd_INT_FILELIST[c_o_i])
                c_o_i = c_o_i+1
            else:
                STIM_LIST.append(even_INT_FILELIST[c_e_i])
                c_e_i = c_e_i+1

        if cond == 'D':
            if C_LIST == 1:
                STIM_LIST.append(even_D_FILELIST[c_e_d])
                c_e_d = c_e_d+1
            else:
                STIM_LIST.append(odd_D_FILELIST[c_o_d]) 
                c_o_d = c_o_d+1

        if cond == 'F':
            if C_LIST == 1:
                STIM_LIST.append(even_F_FILELIST[c_e_f])
                c_e_f = c_e_f+1
            else:
                STIM_LIST.append(odd_F_FILELIST[c_o_f])  
                c_o_f = c_o_f+1
                
    return STIM_LIST

STIM_LIST = get_audios_alice(C_LIST)

TASKS = []
for run_N in range(1, 3):
    for idx in np.arange(len(STIM_LIST_run1)):
        if run_N == 1:
            thisrun = STIM_LIST[0:15]
            if thisrun[idx]!=0:
                TASKS.append(
                    language.Listening(thisrun[idx], wait_key=True, name="test_English"),
                    )
        elif run_N == 2:
            thisrun = STIM_LIST[15:30]
            if thisrun[idx]!=0:
                TASKS.append(
                    language.Listening(thisrun[idx], wait_key=True, name="test_English"),
                    )
        else:
            thisrun = STIM_LIST[30:45]
            if thisrun[idx]!=0:
                TASKS.append(
                    language.Listening(thisrun[idx], wait_key=True, name="test_English"),
                    )

