import os
from ..tasks.things import Things

THINGS_DATA_PATH = os.path.join('data','things')
IMAGE_PATH = os.path.join(THINGS_DATA_PATH,'images')

def get_tasks(parsed):

    session_design_filename = os.path.join(
        THINGS_DATA_PATH, 'designs',
        f"sub-{parsed.subject}_ses-{parsed.session}_design.tsv")
    tasks = [
        Things(
            session_design_filename,
            IMAGE_PATH,
            run,
            name=f"sub-{parsed.subject}_ses-{parsed.session}_run-{run}") \
        for run in range(1,10)
    ]
    return tasks






# experiment

n_sessions              = 12  # number of sessions
n_runs                  = 10  # number of runs
n_trials_exp            = 72  # number of trials for each run
n_trials_catch          = 10  # catch trials where response is required
n_trials_test           = 10  # for test data, separate images
n_trials_total          = n_trials_exp + n_trials_test + n_trials_catch
final_wait              = 9   # time to wait after last trial
initial_wait            = 3   # time until first trial starts

# trial
trial_duration          = 4.5 # mean trial duration
jitters                 = 0   # chosen to be a range that minimizes phase synchrony and that can be presented exactly on most screens
image_duration          = 0.5 # duration of image presentation
rm_duration             = 4.0 # duration of response mapping screen
max_rt                  = 4.0 # from stimulus onset

# constraints
min_catch_spacing = 3
max_catch_spacing = 20

def generate_design_file(subject, session):

    import pandas
    import numpy as np
    images_list = pandas.read_csv(os.path.join(THINGS_DATA_PATH, 'image_paths_fmri.csv'))

    images_exp = images_list[images_list.condition.eq('exp') & images_list.exemplar_nr.eq(session)].sample(frac=1)
    images_catch = images_list[images_list.condition.eq('catch')].sample(frac=1)
    images_test = images_list[images_list.condition.eq('test')].sample(frac=1)

    design = pandas.DataFrame()

    np.random.seed(abs(hash(subject + session))%(2**32 - 1))

    for run in range(n_runs):
        while True:
            randorder = np.random.permutation(n_trials_total)
            n_noncatch_trial = n_trials_exp + n_trials_test
            catch_indices = np.where(randorder >= n_noncatch_trial)[0]
            catch_indices_bounds = np.hstack([[0], catch_indices, [n_trials_total]])
            catch_spacings = np.diff(catch_indices_bounds)
            if np.all(catch_spacings>min_catch_spacing) and \
                np.all(catch_spacings<max_catch_spacing):
                break
        run_trials = pandas.concat([
            images_exp[run*n_trials_exp:(run+1)*n_trials_exp]
            images_catch,
            images_test
            ])
        run_trial = run_trials[randorder]
        pandas.





if __name__ == 'main':
    generate_design_file()
