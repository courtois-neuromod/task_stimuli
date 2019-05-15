from ..tasks import language, task_base

TASKS = [
    language.Triplet(
        'data/language/triplet/first1000triples.csv',
        wait_key=True,
        name='triplet_test')
    ]
