import os
import re
import scipy.io
import numpy as np
import pandas
from word_similarity_matrix import generate_similarity_matrix
from fixed_size_clustering import generate_fixed_size_clusters

# Easy copy paste for ipython.
session = '01'
subject = '01'
run_idx = 1
neuromod_image_list_csv_path = os.path.join('..', '..', '..', 'data', 'things', 'images', 'image_paths_fmri.csv')
sensevec_augmented_file_path = os.path.join('..', '..', '..', 'data', 'prisme', 'things-metadata', 'Semantic Embedding', 'sensevec_augmented_with_wordvec.mat')
things_cats_file_path = os.path.join('..', '..', '..', 'data', 'prisme', 'things-metadata', 'Variables', 'unique_id.csv')

# True vars.
neuromod_image_list_csv_path = os.path.join('data', 'things', 'images', 'image_paths_fmri.csv')
sensevec_augmented_file_path = os.path.join('data', 'prisme', 'things-metadata', 'Semantic Embedding', 'sensevec_augmented_with_wordvec.mat')
things_cats_file_path = os.path.join('data', 'prisme', 'things-metadata', 'Variables', 'unique_id.csv')

def generate_design_file(subject: str, session: str):
    session_index = int(session)

    # Load neuromod/prisme subset of things image dataset
    neuromod_image_list = pandas.read_csv(neuromod_image_list_csv_path)
    neuromod_session_image_list = neuromod_image_list[
        # @note we load all from images_fmri folder, even for test images which
        # we could use from images_test_fmri.
        neuromod_image_list.condition.eq("exp") &
        neuromod_image_list.exemplar_nr.eq(session_index)
    ]

    # Load word embedding vectors.
    sensevec_augmented_file = scipy.io.loadmat(sensevec_augmented_file_path)  # @todo use csv instead
    things_cats = pandas.read_csv(things_cats_file_path, header=None)
    sensevec_augmented = sensevec_augmented_file['sensevec_augmented']

    # Labels word embedding vectors with things cats.
    sensevec_augmented_pd = pandas.DataFrame(data=sensevec_augmented, index=things_cats.values.flatten())

    # Reduce to neuromod/prisme subset of things image dataset.
    path_to_cat_regex = re.compile('[^/]+/([^/]+)/.+')
    neuromod_image_cats = neuromod_session_image_list['image_path']
    neuromod_image_cats = neuromod_image_cats.apply(lambda path: path_to_cat_regex.match(path).group(1))
    neuromod_sensevec_augmented_pd = sensevec_augmented_pd.loc[neuromod_image_cats]

    # Drop na from sensevec fields without synsets vector values.
    # Removes `ready_meal` which has NaN pearson coeff and breaks the
    # clustering. NaN happens when synset vector is filled with same value or
    # contain NaN itself.
    # cf. https://www.kaggle.com/general/186524.
    clean = neuromod_sensevec_augmented_pd.dropna()
    dropped = neuromod_sensevec_augmented_pd[~neuromod_sensevec_augmented_pd.index.isin(clean.index)]
    neuromod_sensevec_augmented_pd = clean
    print('dropped sensevec fields due to lack of synsets value (n/a cells):')
    print(dropped)
    print('neuromod sensevec augmented:')
    print(neuromod_sensevec_augmented_pd)

    # Generate pearson similarity matrix out of the synsets.
    similarity_matrix = generate_similarity_matrix(neuromod_sensevec_augmented_pd)
    print('similarity matrix:')
    print(similarity_matrix)

    # Generate 10 clusters out of the similarity matrix, 5 for shown images to
    # be tested, 5 for unshown images to be tested.
    cluster_count = 10
    test_clusters = generate_fixed_size_clusters(neuromod_sensevec_augmented_pd, similarity_matrix, cluster_count)
    print('clusters:')
    print(test_clusters['cluster'])

    # For each run:
    run_count = 9
    for run_idx in range(run_count):
        # Pickup one image out of each test cluster.
        test_images = test_clusters\
            .groupby('cluster')\
            .apply(lambda x: x.sample(1))\
            .drop('dist', axis=1) # should be reprocessed.
        print('images:')
        print(test_images)

        # Remove these images from the clusters to prevent them from appearing in
        # the next runs.
        test_clusters = test_clusters.drop(test_images.index.get_level_values(1), axis=0)

        # Drop the test images from exp sample.
        neuromod_sensevec_augmented_pd = neuromod_sensevec_augmented_pd.copy(deep=True)
        neuromod_sensevec_augmented_pd = neuromod_sensevec_augmented_pd.drop(test_images.index.get_level_values(1), axis=0)

        # Generate 53 clusters for the experiment. # 58 shown - 5 shown already
        # within test!
        cluster_count = 53
        similarity_matrix = similarity_matrix.drop(test_images.index.get_level_values(1), axis=0)
        similarity_matrix = similarity_matrix.drop(test_images.index.get_level_values(1), axis=1)
        exp_clusters = generate_fixed_size_clusters(neuromod_sensevec_augmented_pd, similarity_matrix, cluster_count)
        print('clusters:')
        print(exp_clusters['cluster'])

        # Pickup shown / unshown images to be tested out of it.
        # @warning in case len(test_clusters) > cluster count, some cluster will
        # be ignored.
        cluster_count = 10
        shown_idx = np.random.choice(range(cluster_count), size=int(cluster_count/2), replace=False)
        unshown_idx = np.delete(range(cluster_count), shown_idx)
        shown_images = test_images.iloc[shown_idx]
        unshown_images = test_images.iloc[unshown_idx]
        shown_images = shown_images.droplevel('cluster', axis=0)
        unshown_images = unshown_images.droplevel('cluster', axis=0)
        print('shown test images:')
        print(shown_images)
        print('unshown test images:')
        print(unshown_images)

        # Pickup one image out of each cluster.
        exp_images = exp_clusters\
            .groupby('cluster')\
            .apply(lambda x: x.sample(1))\
            .drop('dist', axis=1) # should be reprocessed.

        # Remove these images from the clusters to prevent them from appearing in
        # the next runs.
        exp_clusters = exp_clusters.drop(exp_images.index.get_level_values(1), axis=0)

        # Randomize order + ensure we have 53 clusters (output might be a little
        # more, since we aim for perfect fixed-size clusters).
        cluster_count = 53
        base_idx = np.random.choice(range(len(exp_images)), size=cluster_count, replace=False)
        exp_images = exp_images.iloc[base_idx]
        exp_images = exp_images.droplevel('cluster', axis=0)
        print('images:')
        print(exp_images)

        # Inject the 5 test/shown images at +- eq. distance.
        # @todo ensure no out of bound indexes are possible
        for i in range(5):
            index = np.random.choice(range(i*int(58/5), (i+1)*int(58/5)), size=1, replace=False)
            index = index[0]
            shown_image = shown_images.iloc[i].to_frame().transpose()  # ensuring it stays a dataframe, not a series.
            exp_images = pandas.concat([exp_images.iloc[:index], shown_image, exp_images.iloc[index:]])

        print("run %d:" % run_idx)
        print(exp_images)

# Main function.
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
