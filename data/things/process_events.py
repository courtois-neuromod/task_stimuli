import glob
import pandas as pd 
import numpy as np


in_path = "/home/mstlaure/Documents/Marie/neuromod/tests/cneuromod-things/THINGS/fmriprep/sourcedata/things"
out_path = "/home/mstlaure/Documents/Marie/neuromod/scanner_tasks/git/task_stimuli/data/things/memory_designs"

sub_list = ["01", "02", "03", "06"]
clist = ['image_path', 'condition', 'image_nr', 'category_nr', 'exemplar_nr', 'test_image_nr', 'things_category_nr', 'things_image_nr', 'things_exemplar_nr', 'subcondition', 'repetition', 'run', 'onset', 'duration', 'response_mapping_flip_h', 'response_mapping_flip_v']

for s in sub_list:
    for ses in range(1,37):
        f_plist = sorted(glob.glob(f'{in_path}/sub-{s}/ses-{ses:02}/func/*tsv'))
        if len(f_plist):
            f_list = []
            for f in f_plist:
                df = pd.read_csv(f, sep = '\t')
                df = df.rename(columns={"run_id": "run"})
                df = df[clist]
                f_list.append(df)
            pd.concat(f_list, axis=0, ignore_index=True).to_csv(
                f"{out_path}/sub-{s}_ses-{ses:03}_design.tsv", sep='\t', header=True, index=False)


# source /home/mstlaure/Documents/Marie/neuromod/scanner_tasks/git/things_venv/bin/activate
# python main.py --subject 01 --session 001 --tasks thingsmem -o /home/mstlaure/Documents/Marie/neuromod/scanner_tasks/git/task_stimuli/output/thingsmem

"""
Screen size (window, fMRI)
1280, 1024
w, h

config, screen, EXP_WINDOW...?
1920, 1080

eyetracking:
Full screen is 1280:1024
"""
