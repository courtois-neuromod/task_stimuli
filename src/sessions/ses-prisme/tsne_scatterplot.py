# @warning untested

# Load graph deps.
import seaborn as sns
import matplotlib.pyplot as plt

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



# # Display word embedding scatterplot with clusters.
# palette = sns.color_palette('bright', n_colors=len(clusters)+1) # +1 for unclustered items
# plt.clf()
# plot = sns.scatterplot(
#     data=sensevec_augmented_pd,
#     x="x", y="y",
#     hue="cluster",
#     style="cluster",
#     palette=palette,
#     legend=False,
#     alpha=0.8
# )
# # Add text besides each point
# for line in range(0,sensevec_augmented_pd.shape[0]):
#     plot.text(sensevec_augmented_pd['x'][line]+0.01, sensevec_augmented_pd['y'][line], 
#             sensevec_augmented_pd['cluster'][line], horizontalalignment='left', 
#             size=8, color=palette[sensevec_augmented_pd['cluster'][line]+1], weight='light')
# plt.show()
