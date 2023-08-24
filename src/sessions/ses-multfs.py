from ..tasks import multfs

def get_tasks(parsed):

    data_path = "./data/multfs/"
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
