import os

EMOTION_DATA_PATH = "data/emotions" #TBD
VIDEOS_PATH = "data/emotions/clips" #TBD
REPEATED_VIDEOS_PATH = "data/emotions/clips_repeated" #TBD
OUTPUT_RUNS_PATH = "design_runs"
OUTPUT_RUNS_ORDER_PATH = "design_runs_order"

def get_tasks(parsed):
    from ..tasks.emotionvideos import EmotionVideos
    from ..tasks import task_base
    import pandas as pd
    import json

    sub_design_filename = os.path.join(
        EMOTION_DATA_PATH,
        OUTPUT_RUNS_ORDER_PATH,
        f"sub-{parsed.subject}_design_run_order.tsv",
    )

    sub_design = pd.read_csv(sub_design_filename, dtype = {"session" : "str"}, sep="\t", index_col=0)
    bids_sub = "sub-%s" % parsed.subject
    savestate_path = os.path.abspath(os.path.join(parsed.output, "sourcedata",bids_sub, f"{bids_sub}_phase-stable_task-emotionvideos_savestate.json"))

    # check for a "savestate"
    if os.path.exists(savestate_path):
        with open(savestate_path) as f:
            savestate = json.load(f)
    else:
        savestate = {"index": 1}

    for run, design in enumerate(range(savestate['index'], len(sub_design))):
        #load design file for the run according to each participant predefine runs order
        next_run = os.path.join(
            EMOTION_DATA_PATH,
            OUTPUT_RUNS_PATH,
            sub_design.tsv[sub_design.session=="{}{}".format("00", design)].iloc[0])

        task = EmotionVideos(
            next_run,
            REPEATED_VIDEOS_PATH,
            savestate,
            name=f"task-emotionvideos_run-{savestate['index']:02d}",
            use_eyetracking=True,
            target_duration=TARGET_GIFS_DURATION + initial_wait + final_wait,

        )
        yield task

        #only increment if the task was not interrupted. If interrupted, it needs to be rescan
        if task._task_completed:
            savestate['index'] += 1
            with open(savestate_path, 'w') as f:
                json.dump(savestate, f)


# Experiment parameters
random_state = 0
n_runs = 2
initial_wait = 6
final_wait = 9
fixation_duration = 1.5 #seconds
dimensions = ['approach', 'arousal',
   'attention', 'certainty', 'commitment', 'control', 'dominance',
   'effort', 'fairness', 'identity', 'obstruction', 'safety', 'upswing',
   'valence']

#Run
run_min_duration = 345 #seconds of Gifs (doesn't include the ITI)
run_max_duration = 450 #seconds of Gifs (doesn't include the ITI)
iti_min = 3
iti_max = 6
ls_gifs_to_repeat = ["0290.mp4", "1791.mp4"]
time_to_repeat = 3
duration_min = 1
TARGET_GIFS_DURATION = 490 #slightly over the split of total duration to help the search
TOTAL_RUN_NUMBER = 36
RUN_DURATION_THR = 4

# the seed that get the working design with constraint
MAGIC_SEED = 45064


def repeat_gifs(path_to_gifs = VIDEOS_PATH, new_path_to_gifs=REPEATED_VIDEOS_PATH):
    import pandas as pd
    import shutil

    gifs_list = pd.read_csv(
        os.path.join(EMOTION_DATA_PATH, "emotionvideos_path_fmri.csv")
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

    gifs_list.to_csv(os.path.join(EMOTION_DATA_PATH, "emotionvideos_path_fmri.csv"), index=False)

    for idx, row in gifs_list.iterrows():
        path_gif = os.path.join(path_to_gifs, row.Gif)
        new_path_gif = os.path.join(new_path_to_gifs, row.Gif)
        if row.repetition > 0:
            if os.path.isfile(path_gif):
                os.system("ffmpeg -stream_loop {0} -i {1} -c copy {2}".format(row.repetition, path_gif, new_path_gif))
        else :
            if os.path.isfile(path_gif):
                shutil.copy(path_gif, new_path_gif, follow_symlinks=False)


def generate_design_file():
    """
    Generate design files comprising the content of each run
    """

    import pandas as pd
    import numpy as np
    import random
    import math
    from scipy.stats import geom, ks_2samp

    gifs_list = pd.read_csv(
        os.path.join(EMOTION_DATA_PATH, "emotionvideos_path_fmri.csv")
    )
    # seed for ITIs
    np.random.seed(123456789)
    gifs_list['iti'] = geom.rvs(0.8, iti_min-1, size=len(gifs_list), random_state=random_state)

    #split the total duration to a number close to 36, so that all runs have similar length
    tot_gif_dur = gifs_list.duration.sum() + gifs_list.iti.sum()
    target_run_num = int(np.round(tot_gif_dur/TARGET_GIFS_DURATION))
    print(f"total_duration {tot_gif_dur}, aiming for {target_run_num} runs of {tot_gif_dur/target_run_num}")

    # try that a bunch of times
    for i in range(MAGIC_SEED, 1000000):
        #randomize
        np.random.seed(i)
        gifs_rand = gifs_list.sample(frac=1).reset_index()
        csum = np.asanyarray((gifs_rand.total_duration + gifs_rand.iti).cumsum() - gifs_rand.iti)

        splits=[]
        last_split = 0
        # search for splits close to ideal splits
        fail = False
        for sp in range(target_run_num-1):
            cond = np.abs(csum-last_split-TARGET_GIFS_DURATION)
            if not any(cond<RUN_DURATION_THR):
                fail = True
                break
            splits.append(np.argmin(cond))
            last_split = csum[splits[-1]]
        if fail:
            # abort not found
            #print(f'fail {sp}')
            continue
        # check last split
        if np.abs(csum[-1] - last_split-TARGET_GIFS_DURATION) > RUN_DURATION_THR:
            continue
        splits.append(len(gifs_rand)-1)

        start = 0
        last_split = 0
        for run_id, split in enumerate(splits):
            gifs_run = gifs_rand[start:split+1]
            for dimension in dimensions:
                ks_val, ks_p = ks_2samp(gifs_run[dimension], gifs_list[dimension])
                if ks_p < 0.05:
                    print(ks_p)
                    fail = True
                    break
            start=split+1
        if fail:
            continue

        print(f"found design at iteration {i}") #yeahhhh!
        break
    print(gifs_rand.shape)
    print(splits[-1])

    start = 0
    last_split = 0
    duration_of_scan = 0
    for run_id, split in enumerate(splits):

        gifs_run = gifs_rand[start:split+1]
        gifs_run['onset'] = initial_wait + np.cumsum([0] + gifs_run.duration[:-1].tolist()) + np.cumsum([0] + gifs_run.iti[:-1].tolist())
        gifs_run['onset_fixation'] = gifs_run.onset - fixation_duration
        out_fname = os.path.join(
            EMOTION_DATA_PATH,
            OUTPUT_RUNS_PATH,
            f"run-{run_id+1:02d}_design.tsv"
        )

        gifs_run.to_csv(out_fname, sep="\t", index=False)

        print(start,split, csum[split]-last_split, float(gifs_run.onset[-1:] + gifs_run.duration[-1:]) + final_wait)
        start=split+1
        last_split = csum[split]
        duration_of_scan = max(duration_of_scan, float(gifs_run.onset[-1:] + gifs_run.duration[-1:]) + final_wait)

    print(f"Duration of fMRI run = {duration_of_scan}")

def generate_individual_design_file():
    """
    Generate individual design file including the randomized run order for each subject
    """
    import pandas as pd
    import random

    #Assign pseudo-random run order for each participant
    for sub in range(1,7):

        sub_randomized = list(range(1,TOTAL_RUN_NUMBER+1))
        random.seed(sub)
        random.shuffle(sub_randomized)

        tsv_files = [f"run-{filename:02d}_design.tsv" for filename in sub_randomized]
        session = [str(item).zfill(3) for item in range(1,TOTAL_RUN_NUMBER+1)]

        sub_dict = {"session": session,"tsv":tsv_files}

        #Create directory
        if not os.path.exists(os.path.join(EMOTION_DATA_PATH,OUTPUT_RUNS_ORDER_PATH)):
            os.makedirs(os.path.join(EMOTION_DATA_PATH,OUTPUT_RUNS_ORDER_PATH))

        out_fname = os.path.join(
            EMOTION_DATA_PATH,
            OUTPUT_RUNS_ORDER_PATH,
            f"sub-{sub:02d}_design_run_order.tsv"
        )

        gifs_sub = pd.DataFrame(sub_dict)

        gifs_sub.to_csv(out_fname, sep="\t")


if __name__ == "__main__":
    """
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="generate design files for participant / session",
    )
    parser.add_argument("subject", help="participant id")
    parser.add_argument("session", help="session id")
    parsed = parser.parse_args()
    """
    #repeat_gifs()
    generate_design_file()
    generate_individual_design_file()

    #get_tasks(parsed)
