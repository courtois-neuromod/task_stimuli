import os
from ..tasks import multfs
from ..tasks.task_base import Pause
import pandas as pd

data_path = "./data/multfs"

def get_tasks(parsed):

    study_design = pd.read_csv(
        os.path.join(data_path, 'study_designs', f"sub-{int(parsed.subject):02d}_design.tsv"),
        delimiter='\t')


    session_runs = study_design[study_design.session.eq(int(parsed.session))]

    print("*"*100)
    print("Today we will run the tasks in the following order")
    print('- func_task-dms')
    for ri, runs in session_runs.iterrows():
        print(f"- func_task-{runs.block_file_name.split('_')[0]}")

    yield multfs.multfs_dms(
        os.path.join(data_path, "updated_cond_file/pilot_DMS_loc.csv"),
        name = f"task-dmsloc_run-01",
        feature='loc',
        use_eyetracking=True,
        et_calibrate=True, # first task
    )

    tasks_idxs = {
        'interdms': 0,
        'ctxdm': 0,
        'nback': 0
    }

    for ri, (_, runs) in enumerate(session_runs.iterrows()):

        kwargs = {
            'use_eyetracking':True,
            'et_calibrate': ri == 2
            }

        if ri==2:
            yield Pause(
                text="You can take a short break.\n\n Please press A when ready to continue",
                wait_key='a',
            )

        block_file_name = runs.block_file_name
        feat = block_file_name.split('_')[1] # TODO get consistent filenaming!
        run_design_path = os.path.join(data_path, "updated_cond_file/blockfiles/", block_file_name + '.csv')
        if 'interdms' in block_file_name:
            tasks_idxs['interdms'] += 1
            order = block_file_name.split('_')[2]
            kls = multfs.multfs_interdms_ABAB if order == 'ABAB' else multfs.multfs_interdms_ABBA
            yield kls(
                run_design_path,
                name = f"task-interdms{feat}{order}_run-{tasks_idxs['interdms']:02d}",
                feature = feat,
                **kwargs
            )
        elif 'ctxdm' in block_file_name:
            tasks_idxs['ctxdm'] += 1
            yield multfs.multfs_CTXDM(
                run_design_path,
                name = f"task-ctx{feat}_run-{tasks_idxs['ctxdm']:02d}",
                feature=feat,
                **kwargs
            )
        elif 'nback' in block_file_name:
            tasks_idxs['nback'] += 1
            yield multfs.multfs_1back(
                run_design_path,
                name = f"task-1back{feat}_run-{tasks_idxs['nback']:02d}",
                feature=feat,
                **kwargs
            )
