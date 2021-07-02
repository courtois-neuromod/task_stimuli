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

session=1
subject=1

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

# Set plotting env variable for itermplot (platform specific)
# @warning will break matplotlib if itermplot is not installed (most likely)
# @warning doesn't seems to work on OSX
# os.environ['ITERMPLOT_LINES']=str(140)
# os.environ['MPLBACKEND']="module://itermplot"

# Load word embedding vectors + labels.
import scipy.io
import numpy as np
mat = scipy.io.loadmat('data/prisme/things-metadata/Semantic Embedding/sensevec_augmented_with_wordvec.mat')
things_cats = pandas.read_csv('data/prisme/things-metadata/Variables/unique_id.csv', header=None)

# Load graph deps.
import seaborn as sns
import matplotlib.pyplot as plt

sensevec_augmented = mat['sensevec_augmented']
sensevec_augmented_pd = pandas.DataFrame(data=sensevec_augmented, index=things_cats.values.flatten())

# Only use the cneuromod/things subset dataset instead of the whole one.
import re
path_to_cat_regex = re.compile('[^/]+/([^/]+)/.+')
image_cats = images['image_path']
image_cats = image_cats.apply(lambda path: path_to_cat_regex.match(path).group(1))
# image_cats = image_cats.unique()
sensevec_augmented_pd = sensevec_augmented_pd.loc[image_cats]
sensevec_augmented_pd = sensevec_augmented_pd.dropna() # drop na

# Display word embedding scatterplot.
# @warning random, unreliable parameters and result, only for visualization
# (and visualization thus wont be fully representative of the clustering
# efficiency/defects!). Still we do expect sever outliers in the late-processed
# clusters.
import sklearn.manifold
tsne = sklearn.manifold.TSNE(perplexity=50, n_iter=2000, learning_rate=600)
tsne_results = tsne.fit_transform(sensevec_augmented_pd)
tsne_pd = pandas.DataFrame()
sensevec_augmented_pd['x'] = tsne_results[:,0]
sensevec_augmented_pd['y'] = tsne_results[:,1]
# plt.figure(figsize=(16,10))
sns.scatterplot(
    data=sensevec_augmented_pd,
    x="x", y="y",
    #hue="y",
    #palette=sns.color_palette("hls", 10),
    # legend="full",
    # alpha=0.3
)
plt.show()

# Calculate pearson coef. cf. https://stackoverflow.com/questions/33703361/efficiently-calculate-and-store-similarity-matrix
# @todo !! use dropna version instead!! (safer)
pearson_similarity_matrix = np.corrcoef(mat['sensevec_augmented'])

# Inject image path as matrix rows and columns label.
pearson_labeled_similarity_matrix = pandas.DataFrame(data=pearson_similarity_matrix, index=things_cats.values.flatten(), columns=things_cats.values.flatten())

# Only use the cneuromod/things subset dataset instead of the whole one.
import re
path_to_cat_regex = re.compile('[^/]+/([^/]+)/.+')
image_cats = images['image_path']
image_cats = image_cats.apply(lambda path: path_to_cat_regex.match(path).group(1))
# image_cats = image_cats.unique()
filtered_pearson_labeled_similarity_matrix = pearson_labeled_similarity_matrix.loc[image_cats, image_cats]
filtered_pearson_labeled_similarity_matrix

# Draw matrix.
f, ax = plt.subplots(figsize=(11, 9))
sns.heatmap(filtered_pearson_labeled_similarity_matrix, square=True)
plt.show()

# # Change matrix to upper triangle only (in order to be able to change to
# # unidimensional later on).
# # pearson_similarity_matrix = np.triu(pearson_similarity_matrix)
# filter_mask = np.triu(np.ones(filtered_pearson_labeled_similarity_matrix.shape), k=1).astype(bool) # take the lower triangle
# filtered_pearson_labeled_similarity_vector = filtered_pearson_labeled_similarity_matrix.where(filter_mask)

# # Generate unidimensional distance vector from bidimensional distance
# # matrix with metadata about related image path pair.
# filtered_pearson_labeled_similarity_vector = filtered_pearson_labeled_similarity_vector.unstack() # flatten
# filtered_pearson_labeled_similarity_vector = filtered_pearson_labeled_similarity_vector.dropna()

# Removes NaN rows/columns (Removes `ready_meal` which has NaN pearson coeff and breaks the clustering).
# NaN happens when synset vector is filled with same value or contain NaN itself
# cf. https://www.kaggle.com/general/186524.
#filtered_pearson_labeled_similarity_matrix2 = filtered_pearson_labeled_similarity_matrix.fillna(0)
filtered_pearson_labeled_similarity_matrix2 = filtered_pearson_labeled_similarity_matrix.dropna(axis=0, how='all').dropna(axis=1, how='all')

# (kind of) Reduce to single dimension through hierarchical clustering.
# https://stats.stackexchange.com/a/118354
# @todo ensure single is best parameter
#filtered_pearson_labeled_similarity_cluster = scipy.cluster.hierarchy.linkage(filtered_pearson_labeled_similarity_matrix2, optimal_ordering=True)
# @note some methods seems to give good result but are not recommanded as we
# use pearson coef instead of euclidian distance.
# We do use the `complete` method to maximize the consideration of the outliers
# which will be important in order to get fixed-size cluster (further
# explications later steps), while perhaps not being the most optimal choice.
filtered_pearson_labeled_similarity_cluster = scipy.cluster.hierarchy.linkage(filtered_pearson_labeled_similarity_matrix2, method='complete', optimal_ordering=True)

# Plot dendogram.
scipy.cluster.hierarchy.dendrogram(filtered_pearson_labeled_similarity_cluster)
plt.show()
# Plot a prettier one.
# @warning might display different result than propper output `filtered_pearson_labeled_similarity_cluster`
# @note method should be useless, as we use xxx_linkage.
sns.clustermap(filtered_pearson_labeled_similarity_matrix2, method='complete', row_linkage=filtered_pearson_labeled_similarity_cluster, col_linkage=filtered_pearson_labeled_similarity_cluster)
plt.show()

# Reorder matrix.
similarity_cluster_ordered_indexes = scipy.cluster.hierarchy.leaves_list(filtered_pearson_labeled_similarity_cluster)
ordered_similarity_matrix = filtered_pearson_labeled_similarity_matrix2.iloc[similarity_cluster_ordered_indexes, similarity_cluster_ordered_indexes]
ordered_similarity_matrix

# -- constant-size hierarchical clustering
similarity_matrix = ordered_similarity_matrix.copy(deep=True)
desired_clust_count = 10 # n_trials_shown + n_trials_neg
desired_clust_size = len(similarity_matrix) / desired_clust_count # 11
desired_clust_size = math.floor(desired_clust_size)
rest_nb_items = len(similarity_matrix) % desired_clust_size
clusters = []
# Get same-size cluster using the hierarchical clustering.
# http://jmonlong.github.io/Hippocamplus/2018/06/09/cluster-same-size/#iterative-bottom-leaves-hierarchical-clustering
# get fixed-sized clusters
# @warning this is hierarchical, so different rows/clusters can refer to the
# same embedded values.
def pick_leftmost_cluster_by_size(tree, size):
    # @warning can return > size when no cluster of the same size has been found.
    # @note result will likely be truncated to the right size by the fn user.
    # @todo find smallest dist cluster instead (tree.dist) - although suboptimal
    # solution might be better as early optimal solution might mean late
    # suboptimal ones.

    # Search for fixed-size subtree.
    
    # Return cluster if size is good.
    if tree.count == size:
        return tree
    
    # Return none if tree is already too small for what we're looking for.
    if tree.count < size:
        return None

    # Otherwise, first traverse left and seek same-size cluster.
    subtree = pick_leftmost_cluster_by_size(tree.left, size)
    if subtree is not None:
        return subtree # we found it!
    
    # Otherwise traverse right.
    subtree = pick_leftmost_cluster_by_size(tree.right, size)
    if subtree is not None:
        return subtree # we found it!

    # If no cluster has been found yet, redo with higher expected size!
    return pick_leftmost_cluster_by_size(tree, size+1)
def get_leaves_from_tree(tree):
    return tree.pre_order(lambda node: node.id)

# Find first cluster.
tmp_similarity_matrix = similarity_matrix.copy(deep=True) # clone
cluster_linkage_matrix = scipy.cluster.hierarchy.linkage(tmp_similarity_matrix, method='complete', optimal_ordering=True) # gen clust
cluster_tree = scipy.cluster.hierarchy.to_tree(cluster_linkage_matrix) # gen tree
leftmost_fixed_size_cluster = pick_leftmost_cluster_by_size(cluster_tree, desired_clust_size) # get clust
while leftmost_fixed_size_cluster is not None:
    # Add retrieved cluster.
    leftmost_fixed_size_cluster_leaves_idx = get_leaves_from_tree(leftmost_fixed_size_cluster) # get clust idx
    leftmost_fixed_size_cluster_leaves_labels = tmp_similarity_matrix.iloc[leftmost_fixed_size_cluster_leaves_idx].index # get clust labels
    leftmost_fixed_size_cluster_leaves_labels = leftmost_fixed_size_cluster_leaves_labels.to_list()
    del leftmost_fixed_size_cluster_leaves_labels[desired_clust_size:] # truncate if size is too high
    assert len(leftmost_fixed_size_cluster_leaves_labels) == desired_clust_size, "%d != %d" % (len(leftmost_fixed_size_cluster_leaves_labels), desired_clust_size)
    print(leftmost_fixed_size_cluster_leaves_labels)
    clusters.append(leftmost_fixed_size_cluster_leaves_labels) # store clust labels

    # Drop cluster from similarity matrix.
    tmp_similarity_matrix.drop(labels=leftmost_fixed_size_cluster_leaves_labels, axis=0, inplace=True) # drop labels for next iter.
    tmp_similarity_matrix.drop(labels=leftmost_fixed_size_cluster_leaves_labels, axis=1, inplace=True) # drop labels for next iter.

    # Regenerate hierarchical clustering and find next fixed-size cluster.
    cluster_linkage_matrix = scipy.cluster.hierarchy.linkage(tmp_similarity_matrix, method='complete', optimal_ordering=True) # regen clust
    cluster_tree = scipy.cluster.hierarchy.to_tree(cluster_linkage_matrix) # regen tree
    leftmost_fixed_size_cluster = pick_leftmost_cluster_by_size(cluster_tree, desired_clust_size) # reget clust
clusters
flattened_clusters = [item for sublist in clusters for item in sublist]
dups = {i:flattened_clusters.count(i) for i in flattened_clusters}
assert len(clusters) >= desired_clust_count, "%d < %d" % (len(clusters), desired_clust_count)
curr_nb_items = len(flattened_clusters)
exp_nb_items = len(similarity_matrix)
assert curr_nb_items + rest_nb_items == exp_nb_items, "%d + %d != %d" % (curr_nb_items, rest_nb_items, exp_nb_items)

# Display word embedding scatterplot with clusters.
words = sensevec_augmented_pd.index
clusters_by_index = []
for word in words:
    found = False
    for idx, cluster in enumerate(clusters):
        if word in cluster:
            clusters_by_index.append(idx)
            found = True
            break
    if found == False:
        clusters_by_index.append(-1)
sensevec_augmented_pd['cluster'] = clusters_by_index
palette = sns.color_palette('bright', n_colors=len(clusters)+1) # +1 for unclustered items
plt.clf()
plot = sns.scatterplot(
    data=sensevec_augmented_pd,
    x="x", y="y",
    hue="cluster",
    style="cluster",
    palette=palette,
    legend=False,
    alpha=0.8
)
# Add text besides each point
for line in range(0,sensevec_augmented_pd.shape[0]):
    plot.text(sensevec_augmented_pd['x'][line]+0.01, sensevec_augmented_pd['y'][line], 
            sensevec_augmented_pd['cluster'][line], horizontalalignment='left', 
            size=8, color=palette[sensevec_augmented_pd['cluster'][line]+1], weight='light')
plt.show()

# Sort according to hierarchical clustering.
# @warning @todo make sure idx are eq.
sorted_sensevec_augmented_pd = sensevec_augmented_pd.loc[flattened_clusters]

# Add distance between each word.
# @todo make this circular, grouped by cluster, as mean / avg stats will have
# window effect otherwise.
sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd.index[0], 'dist'] = None
for i in range(1, len(sorted_sensevec_augmented_pd)):
    sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd.index[i], 'dist'] = similarity_matrix.loc[sorted_sensevec_augmented_pd.iloc[i-1].name, sorted_sensevec_augmented_pd.iloc[i].name]

# Add avg cluster distance
for cluster_idx in sorted_sensevec_augmented_pd['cluster'].unique():
    sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd['cluster'] == cluster_idx, 'avg_dist'] = sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd['cluster'] == cluster_idx, 'dist'].mean()
    sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd['cluster'] == cluster_idx, 'std_dist'] = sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd['cluster'] == cluster_idx, 'dist'].std()
    sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd['cluster'] == cluster_idx, 'sum_dist'] = sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd['cluster'] == cluster_idx, 'dist'].sum()

sorted_sensevec_augmented_pd.groupby(['cluster']).max()