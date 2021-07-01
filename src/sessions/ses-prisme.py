import os
import math

THINGS_DATA_PATH = os.path.join("data", "things")
PRISME_DATA_PATH = os.path.join("data", "prisme")
IMAGE_PATH = os.path.join(THINGS_DATA_PATH, "images")

# 3 conditions: exp, pos, neg
# shown = image seen by the user
# test:
# pos = test image user is expected to recognize, as he's seen it.
# neg = test image user is expected to not recognize, as it wasn't shown.


# experiment

# n_sessions = 12  # number of sessions
# fmri_runs = 1
# eeg_runs = 1
# n_runs = fmri_runs + eeg_runs  # number of runs
# n_trials_shown = 3  # number of trials for each run
# n_trials_pos = 1  # number of trials for each run
# assert n_trials_pos < n_trials_shown
# n_trials_neg = 1


n_sessions = 12  # number of sessions
assert n_sessions <= 12 # just because input image list csv exemplar_nr max is 12
fmri_runs = 8
eeg_runs = 3
n_runs = fmri_runs + eeg_runs  # number of runs
n_trials_shown = 58  # number of trials for each run
n_trials_pos = 5  # number of trials for each run
assert n_trials_pos < n_trials_shown
n_trials_neg = 5

# n_trials_catch = 0  # catch trials where response is required -- deep dream eq.
# n_trials_test = 2  # for test data, separate images
# n_trials_total = n_trials_shown + n_trials_test # + n_trials_catch
final_wait = 9  # time to wait after last trial
initial_wait = 1.49*2  # time until first trial starts

# trial
trial_duration = 1.49*3  # mean trial duration
jitters = 0  # chosen to be a range that minimizes phase synchrony and that can be presented exactly on most screens
image_duration = 1.49*2  # duration of image presentation
rm_duration = 4.0  # duration of response mapping screen
# max_rt = 4.0  # from stimulus onset
max_rt = 1.49*3

# constraints
# min_catch_spacing = 3
# max_catch_spacing = 20


def get_tasks(parsed):
    from ..tasks.prisme import Prisme

    session_design_filename = os.path.join(
        PRISME_DATA_PATH,
        "designs",
        f"sub-{parsed.subject}_ses-{parsed.session}_design.tsv",
    )
    tasks = [
        Prisme(session_design_filename, IMAGE_PATH, run, name=f"task-prisme_run-{run}")
        for run in range(1, fmri_runs + 1)
    ]
    return tasks


def generate_design_file(subject, session):
    import random
    import hashlib

    # Retrieve image list for session
    # exemplar_nr.eq keeps one cat per session.
    import pandas
    images_list = pandas.read_csv(
        os.path.join(THINGS_DATA_PATH, "images/image_paths_fmri.csv")
    )
    images = images_list[
        images_list.condition.eq("exp") & images_list.exemplar_nr.eq(int(session))
    ].sample(frac=1)

    # images_catch = images_list[images_list.condition.eq("catch")].sample(frac=1)
    # images_test = images_list[images_list.condition.eq("test")].sample(frac=1)

    # 1. trier par ordre sémantique

    # à part
    ## stats pour un run donné - 58 + 5 images selectionnées -- caract sur plan sémantique
    # -- métrique distance moyenne entre image + variance + minimal
    # -- parmis image vue, non vue -- dist. sem, temp. 

    # set plotting env variable for itermplot (platform specific)
    # @warning will break matplotlib if itermplot is not installed (most likely)
    os.environ['ITERMPLOT_LINES']=str(12)
    os.environ['MPLBACKEND']="module://itermplot"

    # Calculate pearson coef. cf. https://stackoverflow.com/questions/33703361/efficiently-calculate-and-store-similarity-matrix
    import scipy.io
    import numpy as np
    mat = scipy.io.loadmat('/Volumes/1ToApfsNVME/things/Semantic Embedding/sensevec_augmented_with_wordvec.mat')
    pearson_similarity_matrix = np.corrcoef(mat['sensevec_augmented'])

    # Inject image path as matrix rows and columns label.
    things_cats = pandas.read_csv('/Volumes/1ToApfsNVME/things/Variables/unique_id.csv', header=None)
    pearson_labeled_similarity_matrix = pandas.DataFrame(data=pearson_similarity_matrix, index=things_cats.values.flatten(), columns=things_cats.values.flatten())

    # Only use the cneuromod/things subset dataset instead of the whole one.
    import re
    path_to_cat_regex = re.compile('[^/]+/([^/]+)/.+')
    image_cats = images['image_path']
    image_cats = image_cats.apply(lambda path: path_to_cat_regex.match(path).group(1))
    image_cats = image_cats.unique()
    filtered_pearson_labeled_similarity_matrix = pearson_labeled_similarity_matrix.loc[image_cats, image_cats]
    # filtered_pearson_labeled_similarity_matrix = pearson_labeled_similarity_matrix.filter(items=image_cats, axis='index') # @warning like != regex -- biais!
    # filtered_pearson_labeled_similarity_matrix = filtered_pearson_labeled_similarity_matrix.filter(items=image_cats, axis='columns')

    # Draw matrix.
    import seaborn as sns
    import matplotlib.pyplot as plt
    f, ax = plt.subplots(figsize=(11, 9))
    sns.heatmap(filtered_pearson_labeled_similarity_matrix, square=True)
    plt.show()

    # Change matrix to upper triangle only (in order to be able to change to
    # unidimensional later on).
    # pearson_similarity_matrix = np.triu(pearson_similarity_matrix)
    filtered_pearson_labeled_similarity_vector = filtered_pearson_labeled_similarity_matrix.iloc[np.triu_indices(len(filtered_pearson_labeled_similarity_matrix))]

    # Generate unidimensional distance vector from bidimensional distance
    # matrix with metadata about related image path pair.
    # @warning items will be present twice if this is taken from the square
    # matrix and not the triangle.
    filtered_pearson_labeled_similarity_vector = filtered_pearson_labeled_similarity_vector.unstack()
    filtered_pearson_labeled_similarity_vector.plot()
    plt.show()

    # Sort by similarity.
    sorted_filtered_pearson_labeled_similarity_vector = filtered_pearson_labeled_similarity_vector.sort_values()

    # Draw vector

    # # Sort by pearson coef
    # import re
    # path_to_cat_regex = re.compile('[^/]+/([^/]+)/.+') # @warning
    # def compare(image_a_obj, image_b_obj):
    #     a_path = image_a_obj['image_path']
    #     a_cat = path_to_cat_regex.match(a_path).group(1)
    #     a_cat_id = things_image_paths.index[things_image_paths[0] == a_path]
    #     b_path = image_b_obj['image_path']
    #     b_cat = path_to_cat_regex.match(b_path).group(1)
    #     b_cat_id = things_image_paths.index[things_image_paths[0] == b_path]
    #     pearson_coeff = psim[a_cat_id][b_cat_id]
    #     return pearson_coeff
    # images.sort_values()


    # @note fixed test size would be better than ratio, as len(images) is
    # already a prepicked subset of image specific to the session.
    split_index = math.floor(len(images) * (1-(n_trials_neg / n_trials_shown)))
    images_exp = images.iloc[0 : split_index]
    images_test = images.iloc[split_index: len(images)]
    print ("images: %s" % len(images))
    print ("ratio: %s" % (n_trials_neg / n_trials_shown))
    print ("shown: %s" % len(images_exp))
    print ("test: %s" % len(images_test))
    assert n_trials_shown <= len(images_exp)
    assert n_trials_neg <= len(images_test)

    design = pandas.DataFrame()

    print("%s-%s" % (subject, session))
    seed = int(
        hashlib.sha1(("%s-%s" % (subject, session)).encode("utf-8")).hexdigest(), 16
    ) % (2 ** 32 - 1)
    print("seed", seed)
    np.random.seed(seed) # @warning seed will be reset between #random calls so probably misworking! @todo checkout

    all_run_trials = pandas.DataFrame()

    for run in range(n_runs):
        # 1. retrieve random images to display for the run.
        niter = 0
        # prevent consecutive catch images.
        # while True:
        #     niter += 1
        #     randorder = np.random.permutation(n_trials_total)
        #     n_noncatch_trial = n_trials_shown + n_trials_test
        #     catch_indices = np.where(randorder >= n_noncatch_trial)[0]
        #     catch_indices_bounds = np.hstack([[0], catch_indices, [n_trials_total]])
        #     catch_spacings = np.diff(catch_indices_bounds)
        #     if not np.all(catch_spacings < min_catch_spacing) or not np.all(
        #         catch_spacings > max_catch_spacing
        #     ):
        #         break
        #     break
        print(subject, session, run, niter)
        # run_trials = run_images_exp.iloc[randorder]
        # run_trials = pandas.concat(
        #     [
        #         images_exp[run * n_trials_shown : (run + 1) * n_trials_shown],
        #         images_test[run * n_trials_test : (run + 1) * n_trials_test],
        #         images_catch[run * n_trials_catch : (run + 1) * n_trials_catch],
        #     ]
        # )
        randorder = np.random.permutation(n_trials_shown)
        shown_images = images_exp[run * n_trials_shown : (run + 1) * n_trials_shown] # retrieve
        shown_images = shown_images.copy(deep=True)
        shown_images = shown_images.iloc[randorder] # randomize
        shown_images["run"] = run + 1
        # shown_images["onset"] = initial_wait + np.arange(n_trials_shown) * trial_duration
        shown_images["duration"] = image_duration
        shown_images["condition"] = "shown"
        shown_images["onset"] = initial_wait + np.arange(n_trials_shown) * trial_duration

        # 2. pick up random images out of the shown ones and mix them up with
        # random test ones.
        # randorder = np.random.permutation(n_trials_total)
        # run_trials_test = 
        # image_pos = images_test[run * n_trials_test : (run + 1) * n_trials_test]

        randorder = np.random.permutation(n_trials_pos)
        positive_images = shown_images.copy(deep=True)
        positive_images = positive_images.iloc[randorder]
        positive_images["run"] = run + 1
        # @todo redefine onset
        # positive_images["onset"] = initial_wait + np.arange(n_trials_shown) * trial_duration  + np.arange(n_trials_pos) * trial_duration
        positive_images["duration"] = image_duration
        positive_images["condition"] = "pos"
        
        randorder = np.random.permutation(n_trials_neg)
        negative_images = images_test[run * n_trials_neg : (run + 1) * n_trials_neg]
        negative_images = negative_images.copy(deep=True)
        negative_images = negative_images.iloc[randorder]
        negative_images["run"] = run + 1
        negative_images["duration"] = image_duration
        negative_images["condition"] = "neg"

        randorder = np.random.permutation(n_trials_pos + n_trials_neg)
        test_images = pandas.concat([positive_images,negative_images])
        test_images = test_images.iloc[randorder]

        all_run_images = pandas.concat([shown_images, test_images])
        all_run_images["onset"] = initial_wait + np.arange(n_trials_shown + n_trials_neg + n_trials_pos) * trial_duration

        all_run_images["type"] = "fmri" if run <= 8 else "eeg"

        all_run_trials = pandas.concat([all_run_trials, all_run_images])

    out_fname_images = os.path.join(
        PRISME_DATA_PATH,
        "designs",
        f"sub-{parsed.subject}_ses-{parsed.session}_design.tsv",
    )
    all_run_trials.to_csv(out_fname_images, sep="\t")


    # out_fname_tests = os.path.join(
    #     PRISME_DATA_PATH,
    #     "designs",
    #     f"sub-{parsed.subject}_ses-{parsed.session}_test_design.tsv",
    # )


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="generate design files for participant / session",
    )
    parser.add_argument("subject", type=str, help="participant id")
    parser.add_argument("session", type=str, help="session id")
    parsed = parser.parse_args()
    generate_design_file(parsed.subject, parsed.session)
