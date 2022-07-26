import os

EMOTION_DATA_PATH = "/Users/mepicard/Documents/neuromod/data/emotion"
#GIFS_PATH = os.path.join(EMOTION_DATA_PATH,"emotionvideos")
VIDEOS_PATH = "/Volumes/LaCie/Cowen/Cowen"


def get_tasks(parsed):
    from ..task.emotionvideos import EmotionVideos
    import pandas as pd
    
    sub_design_filename = os.path.join(
        EMOTION_DATA_PATH,
        "designs_runs_order",
        f"sub-{parsed.subject}_design_run_order.tsv",
    )

    sub_design = pd.read_csv(sub_design_filename, dtype = {"session" : "str"}, sep="\t", index_col=0)

    """

    test[test["session"]=="001"]["tsv"]
    
    tasks = [
        EmotionVideos(session_design_filename, VIDEOS_PATH, run, name=f"task-emotion_run-{run}")
        for run in range(1, n_runs_per_session +1)
    ]
    
    return tasks
    """
    

# Experiment parameters 
random_state = 0
n_runs = 33
n_runs_per_session = 2
initial_wait = 5
final_wait = 5

#trial
run_min_duration = 345 #seconds of Gifs (doesn't include the ITI)
run_max_duration = 450 #seconds of Gifs (doesn't include the ITI)
iti_min = 3
iti_max = 6
ls_gifs_to_repeat = ["0290.mp4", "1791.mp4"]
time_to_repeat = 3
duration_min = 1


def repeat_gifs(path_to_gifs = VIDEOS_PATH, new_path_to_gifs=EMOTION_DATA_PATH):
    import pandas as pd
    import shutil 

    gifs_list = pd.read_csv(
        os.path.join(EMOTION_DATA_PATH, "gifs_path_fmri.csv")
    )

    repetition = []
    for i, row in gifs_list.iterrows():
        if row.duration < duration_min:
            if row.Gif in ls_gifs_to_repeat:
                repetition.append(time_to_repeat//row.duration)
            else:
                repetition.append(duration_min//row.duration)
        elif row.duration >= duration_min:
            repetition.append(0)
    
    gifs_list['repetition'] = repetition

    gifs_list.to_csv(os.path.join(EMOTION_DATA_PATH, "gifs_path_fmri.csv"))

    for idx, row in gifs_list.iterrows():
        path_gif = os.path.join(path_to_gifs, row.Gif)
        new_path_gif = os.path.join(new_path_to_gifs, row.Gif)
        if row.repetition > 0:
            if os.path.isfile(path_gif):
                os.system("ffmpeg -stream_loop {0} -i {1} -c copy {2}".format(row.repetition, path_gif, new_path_gif))
        else :
            if os.path.isfile(path_gif):
                shutil.copy(path_gif, new_path_gif)


def generate_design_file(random_state):
    """
    Generate design files comprising the content of each run
    """

    import pandas as pd
    import numpy as np
    import random
    import math
    from scipy.stats import geom
    
    random.seed(0)
    
    gifs_list = pd.read_csv(
        os.path.join(EMOTION_DATA_PATH, "gifs_path_fmri.csv")
    )
    session = 1

    while not gifs_list.empty:

        gifs_id = []
        total_duration = 0
        #Make sure there's no run with just a few Gifs in it
        if gifs_list.duration.sum() < run_max_duration:
            gifs_id = gifs_list.Gif
        else:
            for i, row in gifs_list.sample(frac=1, random_state=random_state).iterrows():
                #Select Gifs until the total duration reach more than trial_duration
                if (total_duration + row.duration) < run_min_duration:
                    total_duration += row.duration
                    gifs_id.append(row.Gif)
                
        gifs_exp = gifs_list[gifs_list.Gif.isin(gifs_id)]
        gifs_list = gifs_list.drop(gifs_list.index[gifs_list.Gif.isin(gifs_exp.Gif)],axis=0)
        gifs_exp = gifs_exp.reset_index()
                
        iti = geom.rvs(0.5, iti_min-1, size=1000, random_state=random_state)
        iti_n = random.sample(iti[iti<=iti_max].tolist(),len(gifs_exp))
        
        onset = []
        i_temp = 0

        for i, row in gifs_exp.iterrows():
            if i == 0:
                onset.append(initial_wait)
            else:
                onset.append(gifs_exp.duration[i_temp]+onset[i_temp]+iti_n[i_temp])
            i_temp = i
            
        gifs_exp['onset'] = onset
        gifs_exp['iti'] = iti_n

        out_fname = os.path.join(
            EMOTION_DATA_PATH,
            "designs_runs",
            f"run-{session}_design.tsv"
        )
                
        gifs_exp.to_csv(out_fname, sep="\t")

        session += 1


def generate_individual_design_file():
    """
    Generate individual design file including the randomized run order for each subject
    """
    import pandas as pd
    import random

    for sub in range(1,7):

        sub_randomized = list(range(1,n_runs+1))
        random.seed(sub)
        random.shuffle(sub_randomized)

        tsv_files = [f"run-{filename}_design.tsv" for filename in sub_randomized]
        session = [str(item).zfill(3) for item in list(range(1,n_runs+1))]

        sub_dict = {"session": session,"tsv":tsv_files}

        out_fname = os.path.join(
            EMOTION_DATA_PATH,
            "designs_runs_order",
            f"sub-00{sub}_design_run_order.tsv"
        )

        gifs_sub = pd.DataFrame(sub_dict)

        gifs_sub.to_csv(out_fname, sep="\t")

    
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="generate design files for participant / session",
    )
    parser.add_argument("subject", type=str, help="participant id")
    parser.add_argument("session", type=str, help="session id")
    parsed = parser.parse_args()

    generate_design_file(random_state)
    generate_individual_design_file()
    
    
