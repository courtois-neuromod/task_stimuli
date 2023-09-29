import os
import numpy as np
import pandas as pd

basepath = "/Users/xiaoxuan/Dropbox/projects/phd_project/202209_MULTFS_MRI_Simple/202307_task_conds"
taskname = "nback"
filename = "nback_obj"
df = pd.read_csv(os.path.join(basepath, filename +  ".csv"))
n_trials = len(df)
if taskname == "ctxdm":
    trials_per_block = 20
elif taskname == "interdms":
    trials_per_block = 16
elif taskname == "nback":
    trials_per_block = 9

n_blocks = np.int(n_trials/trials_per_block)
df = df.sample(frac=1, random_state=42)

for i in range(n_blocks):
    curr_df = df.iloc[i*trials_per_block:(i+1)*trials_per_block]
    curr_df.to_csv(os.path.join(basepath, "blockfiles",filename + "_block_%d.csv" % i ), index=False)
