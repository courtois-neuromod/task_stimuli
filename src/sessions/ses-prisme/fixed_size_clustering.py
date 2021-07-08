import pandas
import math
import scipy.cluster.hierarchy

def generate_fixed_size_clusters(sensevec_augmented_pd: pandas.DataFrame, similarity_matrix: pandas.DataFrame, cluster_count: int):
    sensevec_augmented_pd = sensevec_augmented_pd.copy(deep=True)

    # -- constant-size hierarchical clustering
    desired_clust_count = cluster_count # n_trials_shown + n_trials_neg
    desired_clust_size = len(similarity_matrix) / desired_clust_count # 11
    desired_clust_size = math.floor(desired_clust_size)
    rest_nb_items = len(similarity_matrix) % desired_clust_size
    clusters = []
    # Get same-size cluster using the hierarchical clustering.
    # inspired by http://jmonlong.github.io/Hippocamplus/2018/06/09/cluster-same-size/#iterative-bottom-leaves-hierarchical-clustering
    # @note this is hierarchical, so different rows/clusters can refer to the same 
    # embedded values.
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
        
        # Log cluster.
        # print(leftmost_fixed_size_cluster_leaves_labels)

        # Store cluster labels.
        clusters.append(leftmost_fixed_size_cluster_leaves_labels) 

        # Drop cluster from similarity matrix.
        tmp_similarity_matrix.drop(labels=leftmost_fixed_size_cluster_leaves_labels, axis=0, inplace=True) # drop labels for next iter.
        tmp_similarity_matrix.drop(labels=leftmost_fixed_size_cluster_leaves_labels, axis=1, inplace=True) # drop labels for next iter.

        # Regenerate hierarchical clustering and find next fixed-size cluster.
        # @note single item distance matrix breaks code, anything less than
        # desired_clust_size is useless.
        if (len(tmp_similarity_matrix) < desired_clust_size):
            leftmost_fixed_size_cluster = None
        else:
            cluster_linkage_matrix = scipy.cluster.hierarchy.linkage(tmp_similarity_matrix, method='complete', optimal_ordering=True) # regen clust
            cluster_tree = scipy.cluster.hierarchy.to_tree(cluster_linkage_matrix) # regen tree
            leftmost_fixed_size_cluster = pick_leftmost_cluster_by_size(cluster_tree, desired_clust_size) # reget clust

    flattened_clusters = [item for sublist in clusters for item in sublist]
    dups = {i:flattened_clusters.count(i) for i in flattened_clusters}
    assert len(clusters) >= desired_clust_count, "%d < %d" % (len(clusters), desired_clust_count)
    curr_nb_items = len(flattened_clusters)
    exp_nb_items = len(similarity_matrix)
    assert curr_nb_items + rest_nb_items == exp_nb_items, "%d + %d != %d" % (curr_nb_items, rest_nb_items, exp_nb_items)

    # Inject clusters' ids within sensevec augmented matrix.
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

    # Sort according to hierarchical clustering.
    # @warning @todo make sure idx are eq.
    sorted_sensevec_augmented_pd = sensevec_augmented_pd.loc[flattened_clusters]

    # Add distance between each word.
    # @WARNING @WARNING @WARNING @WARNING @WARNING @WARNING @WARNING @WARNING
    # @warning                      not for analysis
    # @warning     /!\ these cluster metrics have windows effects /!\
    # @todo make these metrics out of circular list / grouped by cluster instead.
    # @WARNING @WARNING @WARNING @WARNING @WARNING @WARNING @WARNING @WARNING
    sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd.index[0], 'dist'] = None
    for i in range(1, len(sorted_sensevec_augmented_pd)):
        sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd.index[i], 'dist'] = similarity_matrix.loc[sorted_sensevec_augmented_pd.iloc[i-1].name, sorted_sensevec_augmented_pd.iloc[i].name]

    # Add avg cluster distance
    for cluster_idx in sorted_sensevec_augmented_pd['cluster'].unique():
        sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd['cluster'] == cluster_idx, 'avg_dist'] = sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd['cluster'] == cluster_idx, 'dist'].mean()
        sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd['cluster'] == cluster_idx, 'std_dist'] = sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd['cluster'] == cluster_idx, 'dist'].std()
        sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd['cluster'] == cluster_idx, 'sum_dist'] = sorted_sensevec_augmented_pd.loc[sorted_sensevec_augmented_pd['cluster'] == cluster_idx, 'dist'].sum()

    sorted_sensevec_augmented_pd.groupby(['cluster']).max()

    return sorted_sensevec_augmented_pd