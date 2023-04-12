import os
from ..tasks.narratives import Story


STIMULI_PATH = 'data/language/petitprince.stimuli/stimuli/'
N_SEGMENTS = 9
def get_tasks(parsed):

    lang_order = ['FR', 'EN']
    if int(parsed.subject) in [3,5,6]:
        lang_order = lang_order[::-1]


    all_segments = [(lang, seg) for lang in lang_order for seg in range(N_SEGMENTS)]

    for lang,seg in all_segments:
        yield Story(
            sound_file=os.path.join(STIMULI_PATH, f'task-lpp{lang}_section{"_" if lang=="FR" else "-"}{seg+1}.wav'),
            name=f"task-lpp{lang}_run-{seg+1:02d}")
