import os, sys
import pyglet
pyglet.options['audio']=('pulse','directsound', 'openal', 'silent')
from psychopy import visual, core, data

print(pyglet.options['audio'])

from shared import fmri, config

def play_video(filename,window=None):
    if window is None:
        window = visual.Window()
    mov = visual.MovieStim(window, filename)
    print(mov.duration)
    # give the original size of the movie in pixels:
    print(mov.format.width, mov.format.height)

    fmri.wait_for_ttl()
    while True:
        mov.draw()
        window.flip()

window = visual.Window(screen=1,fullscr=True)
play_video('videos/Inscapes-67962604.mp4',
    window=window)
