from ..tasks import multfs

def get_tasks(parsed):

    data_path = "./data/multfs/"
    return [
        multfs.multfs_ctx(data_path + "CTX_category_object_loc_stim4.csv", name = "task-ctxcol_run-01"),
        multfs.multfs_1back(data_path + "1back_loc_4stim_seq6.csv", name="task-1backloc_run-01"),
        multfs.multfs_dms(data_path + "DMS_loc_4stim.csv", name = "task-dmsloc_run-01"),
        multfs.multfs_interdms_AABB(data_path + "interDMS_loc_AABB.csv", name = "task-interdmsloc_AABB_run-01")

        ]
