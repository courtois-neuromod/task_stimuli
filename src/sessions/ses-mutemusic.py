import os
from ..tasks.mutemusic import Playlist

STIMULI_PATH  = 'data/mutemusic'

def get_tasks(parsed):
    #TO-DO: check the last playlist that have been played
    last_playlist = 1

    for pli in range(last_playlist, 7):
        playlist_file = f'Sub-{parsed.subject}_Playlist_{pli}.tsv'
        playlist_path = os.path.join(STIMULI_PATH, f'Sub-{parsed.subject}', playlist_file)
        yield Playlist(
            tsv_path=playlist_path,
            use_eyetracking=True,
            et_calibrate=pli==last_playlist,
            name=f"task-mutemusic_run-{pli}")
