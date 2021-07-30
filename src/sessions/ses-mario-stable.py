
import numpy as np
import random
import hashlib

worlds = 8
levels = 3
exclude_list = [(2,2),(7,2)]
all_levels = [(world, level)
    for world in range(1,worlds+1)
    for level in range(1,levels+1)
    if (world,level) not in exclude_list]
n_repetitions = 50 # very high level, will never reach that point

def randomize_levels(subject):
    import pandas

    seed = int(
        hashlib.sha1(("%s" % (subject)).encode("utf-8")).hexdigest(), 16
    ) % (2 ** 32 - 1)
    print("seed", seed)
    random.seed(seed)

    subject_levels = sum([random.sample(all_levels,len(all_levels)) for rep in range(n_repetitions)],[])
