# @warning untested

# Load graph deps.
import seaborn as sns
import matplotlib.pyplot as plt

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
