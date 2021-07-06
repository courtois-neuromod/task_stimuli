import pandas
import numpy as np
import scipy.cluster.hierarchy


# @params pandas.DataFrame labelled sensevec_augmented synsets matrix without
#                          n/a cells.
def generate_similarity_matrix(sensevec_augmented: pandas.DataFrame):
    # Calculate pearson coef.
    # cf. https://stackoverflow.com/questions/33703361/efficiently-calculate-and-store-similarity-matrix
    pearson_similarity_matrix = np.corrcoef(sensevec_augmented)

    # Inject image path as matrix rows and columns label.
    pearson_labeled_similarity_matrix = pandas.DataFrame(
        data=pearson_similarity_matrix, index=sensevec_augmented.index,
        columns=sensevec_augmented.index)

    # (kind of) Reduce to single dimension through hierarchical clustering in
    # order to sort matrix.
    # https://stats.stackexchange.com/a/118354
    # @note some methods seems to give good result but are not recommanded as we
    # use pearson coef instead of euclidian distance.
    # We do use the `complete` method to maximize the consideration of the outliers
    # which will be important in order to get fixed-size cluster (further
    # explications later steps), while perhaps not being the most optimal choice.
    filtered_pearson_labeled_similarity_cluster = scipy.cluster.hierarchy.linkage(
        pearson_labeled_similarity_matrix, method='complete',
        optimal_ordering=True)

    # Reorder matrix (optional in our case, as we will do clusters afterwards,
    # but helpful for debugging).
    similarity_cluster_ordered_indexes = scipy.cluster.hierarchy.leaves_list(
        filtered_pearson_labeled_similarity_cluster)
    ordered_similarity_matrix = pearson_labeled_similarity_matrix.iloc[
        similarity_cluster_ordered_indexes, similarity_cluster_ordered_indexes]
    
    # Return matrix.
    return ordered_similarity_matrix
