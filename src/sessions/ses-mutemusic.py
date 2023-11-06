import os
from ..tasks.mutemusic import Playlist

STIMULI_PATH  = 'data/mutemusic'

def get_tasks(parsed):
    #TO-DO: check the last playlist that have been played
    last_playlist = 1 
    playlist_file = f'Sub-0{parsed.subject}_Playlist_{last_playlist}.csv'
    playlist_path = os.path.join(STIMULI_PATH, f'Sub-0{parsed.subject}', playlist_file)

    yield Playlist(csv_path=playlist_path)