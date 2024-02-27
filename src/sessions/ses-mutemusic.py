import os
import pandas
from ..tasks.mutemusic import Playlist

STIMULI_PATH  = 'data/mutemusic'

def get_tasks(parsed):
    sub = f'Sub-{parsed.subject}'
    playlists_order_path = os.path.join(STIMULI_PATH, sub, f'{sub}_Playlist_order.tsv')
    playlist_order = pandas.read_csv(playlists_order_path, sep=' ')

    current_playlist = len(playlist_order)
    for i, playlist in playlist_order.iterrows():
        if not playlist['done']:
            current_playlist = i
            break

    playlist_sequence = playlist_order[current_playlist:]
    for i, playlist in playlist_sequence.iterrows():
        pli = playlist['playlist']
        playlist_file = f'{sub}_Playlist_{pli}.tsv'
        playlist_path = os.path.join(STIMULI_PATH, sub, playlist_file)
        yield Playlist(
            tsv_path=playlist_path,
            use_eyetracking=True,
            et_calibrate=i==current_playlist,
            name=f"task-mutemusic_run-{i}")
        
        if playlist._task_completed:
            playlist_order['done'].iloc[i] = 1
            playlist_order.to_csv(playlists_order_path, sep=' ', index=False)