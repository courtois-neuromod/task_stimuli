import os
from ..tasks import multfs
import pandas as pd

data_path = "./data/multfs"

def get_tasks(parsed):

    study_design = pd.read_csv(
        os.path.join(data_path, 'study_designs', f"sub-{int(parsed.subject):02d}_design.tsv"),
        delimiter='\t')


    session_runs = study_design[study_design.session.eq(int(parsed.session))]

    print(session_runs)

    kwargs = {'use_eyetracking':True}


    yield multfs.multfs_dms(
        os.path.join(data_path, "updated_cond_file/pilot_DMS_loc.csv"),
        name = f"task-dmsloc_run-01",
        feature='loc',
        **kwargs
    )



    for ri, runs in session_runs.iterrows():

        block_file_name = runs.block_file_name
        feat = block_file_name.split('_')[1] # TODO get consistent filenaming!
        run_design_path = os.path.join(data_path, "updated_cond_file/blockfiles/", block_file_name + '.csv')
        if 'interdms' in block_file_name:
            order = block_file_name.split('_')[2]
            kls = multfs.multfs_interdms_ABAB if order == 'ABAB' else multfs.multfs_interdms_ABBA
            yield kls(
                run_design_path,
                name = f"task-interdms{feat}{order}_run-01",
                feature = feat,
                **kwargs
            )
        elif 'ctxdm' in block_file_name:
            yield multfs.multfs_CTXDM(
                run_design_path,
                name = f"task-ctx{feat}_run-01",
                feature=feat,
                **kwargs
            )
        elif 'nback' in block_file_name:
            yield multfs.multfs_1back(
                run_design_path,
                name = f"task-1back{feat}_run-01",
                feature=feat,
                **kwargs
            )

import glob
def generate_designs():
    n_blocks_nback = 16
    n_blocks_ctxdm = 16
    n_block_interdms = 10

    blocks_path  = os.path.join(data_path, "updated_cond_file/blockfiles")

    tasks_nback = [
        os.path.split(f).split('.')[0] \
        for f in sorted(glob.glob(os.path.join(blocks_path, "nback_*",))) ]
    tasks_ctxdm_loc = [
        os.path.split(f).split('.')[0] \
        for f in sorted(glob.glob(os.path.join(blocks_path, "ctxdm_loc_*",)))]
    tasks_ctxdm_lco = [
        os.path.split(f).split('.')[0] \
        for f in sorted(glob.glob(os.path.join(blocks_path, "ctxdm_loc_*",)))]

    for ses in range(16):
        ses_tasks = []

"""



    return [
        # for piloting
        multfs.multfs_dms(data_path + "pilot/pilot_DMS_loc.csv", name="task-dmsloc_run-01", feature="loc", session=parsed.session),
        multfs.multfs_CTXDM(data_path + "updated_cond_file/blockfiles/ctxdm_colblock_0.csv",name="task-ctxcol_run-01",feature="col",session=parsed.session),
        multfs.multfs_1back(data_path + "updated_cond_file/blockfiles/nback_ctgblock_0.csv",name = "task-1backcat_run-01",feature="cat", session = parsed.session),
        multfs.multfs_interdms_ABAB(data_path + "updated_cond_file/blockfiles/interdms_ctg_ABABblock_0.csv", name = "task_interdmscat_ABAB_run-00", feature = "cat", session = parsed.session)
        # multfs.multfs_CTXDM(data_path + "pilot/pilot_ctxDM_lco.csv", name="task-ctxlco_run-01", feature="lco",session=parsed.session),
        # multfs.multfs_1back(data_path + "pilot/pilot_1back_loc.csv", name="task-1backloc_run-01", feature="loc", session=parsed.session),


        # for subject task practicing
        # multfs.multfs_dms(data_path + "subtraining/subtraining_dms_loc.csv", name="task-dmsloc_run-00", feature="loc", session=parsed.session),
        #
        # multfs.multfs_1back(data_path + "subtraining/subtraining_1back_cat.csv", name="task-1backcat_run-00", feature="cat", session=parsed.session),
        # multfs.multfs_1back(data_path + "subtraining/subtraining_1back_loc.csv", name="task-1backloc_run-00", feature="loc", session=parsed.session),
        # multfs.multfs_1back(data_path + "subtraining/subtraining_1back_obj.csv", name="task-1backobj_run-00", feature="obj", session=parsed.session),
        #
        # multfs.multfs_CTXDM(data_path + "subtraining/subtraining_ctxdm_lco.csv", name="task-ctxlco_run-00", feature="lco", session=parsed.session),
        # multfs.multfs_CTXDM(data_path + "subtraining/subtraining_ctxdm_col.csv", name="task-ctxcol_run-00", feature="col", session=parsed.session),

        # multfs.multfs_interdms_ABAB(data_path + "subtraining/subtraining_interDMS_ABAB_cat.csv", name="task_interdmscat_ABAB_run-00",feature="cat", session=parsed.session),
        # multfs.multfs_interdms_ABAB(data_path + "subtraining/subtraining_interDMS_ABAB_loc.csv", name="task_interdmsloc_ABAB_run-00", feature="loc", session=parsed.session),
        # multfs.multfs_interdms_ABAB(data_path + "subtraining/subtraining_interDMS_ABAB_obj.csv", name="task_interdmsobj_ABAB_run-00", feature="obj", session=parsed.session),
        #
        # multfs.multfs_interdms_ABBA(data_path + "subtraining/subtraining_interDMS_ABBA_cat.csv", name="task_interdmscat_ABBA_run-00", feature="cat", session=parsed.session),
        # multfs.multfs_interdms_ABBA(data_path + "subtraining/subtraining_interDMS_ABBA_loc.csv", name="task_interdmsloc_ABBA_run-00", feature="loc", session=parsed.session),
        # multfs.multfs_interdms_ABBA(data_path + "subtraining/subtraining_interDMS_ABBA_obj.csv", name="task_interdmsobj_ABBA_run-00", feature="obj", session=parsed.session),

        ]
"""
