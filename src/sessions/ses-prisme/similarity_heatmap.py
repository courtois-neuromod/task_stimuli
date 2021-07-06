# @warning untested

# Load graph deps.
import seaborn as sns
import matplotlib.pyplot as plt

# Draw matrix.
f, ax = plt.subplots(figsize=(11, 9))
sns.heatmap(filtered_pearson_labeled_similarity_matrix, square=True)
plt.show()
