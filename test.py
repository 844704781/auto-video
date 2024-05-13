import numpy as np
from moviepy.editor import VideoFileClip
src = VideoFileClip("t.mp4")
w, h = src.size
duration = src.duration
def fl(gf, t):
    frame = gf(t)
    dh = int(h * t * 3 / duration) % h
    return np.vstack((frame[dh:], frame[:dh]))

newclip = src.fl(fl, apply_to='mask')
newclip.write_videofile("r.mp4")
