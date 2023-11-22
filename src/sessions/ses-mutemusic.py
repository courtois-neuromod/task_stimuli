import os
import json
from ..tasks.mutemusic import Playlist

STIMULI_PATH  = 'data/mutemusic'

def get_tasks(parsed):
    bids_sub = "sub-%s" % parsed.subject
    savestate_path = os.path.join(parsed.output, f"{bids_sub}_phase-stable_task-mutemusic_savestate.json")
    # savestate_path = os.path.abspath(os.path.join(parsed.output, "sourcedata",bids_sub, f"{bids_sub}_phase-stable_task-mutemusic_savestate.json"))
    # check for a "savestate"
    if os.path.exists(savestate_path):
        with open(savestate_path) as f:
            savestate = json.load(f)
    else:
        savestate = {"index": 0}

    for last_playlist in range(savestate['index'], 6):

        playlist_file = f'Sub-{parsed.subject}_Playlist_{last_playlist+1}.tsv'
        playlist_path = os.path.join(STIMULI_PATH, f'Sub-{parsed.subject}', playlist_file)

        playlist = Playlist(tsv_path=playlist_path, name=f"task-mutemusic_run-{last_playlist}")
        yield playlist
        
        if playlist._task_completed:
            savestate['index'] += 1
            with open(savestate_path, 'w') as f:
                json.dump(savestate, f)