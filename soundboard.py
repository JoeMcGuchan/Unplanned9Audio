import random
import pygame
import keyboard
import os

pygame.mixer.init()

SUPPORTED_EXTENSIONS = (".mp3", ".wav", ".ogg", ".flac")

# -------- CONFIG -------- #

# loop: whether or not the music should loop on finishing
# tracks are stored as (track, volume)
KEY_BINDINGS = {
    "1": {
        "loop": True,
        "tracks": [
            (r"Music\1\bbc_common-fro_nhu0510423.mp3", 0.8, 1500),
            (r"Music\1\bbc_peregrine-_nhu0510423.mp3", 0.6, 3000),
        ],
    },
    "2": {
        "loop": False,
        "tracks": [
            (r"Music\2\bbc_hooded-cro_nhu0510419.mp3", 0.7, 0),
            (r"Music\2\bbc_reindeer--_nhu0510415.mp3", 0.5, 2000),
        ],
    },
    "3": {
        "loop": True,
        "tracks": [
            (r"Music\3\bbc_scottish-c_nhu0510409.mp3", 0.9, 1000),
            (r"Music\3\bbc_tawny-owl-_nhu0510408.mp3", 0.65, 4000),
        ],
    },
}

LAST_SONG = {key: None for key in KEY_BINDINGS}

STOP_KEY = "0"
QUIT_KEY = "esc"

# ------------------------ #

def play_random_song(binding, key_id):
    tracks = binding["tracks"]
    loop = binding["loop"]
    last_song = LAST_SONG[key_id]

    # Only exclude the last song
    valid_tracks = [
        (path, volume, fade)
        for path, volume, fade in tracks
        if os.path.isfile(path)
        and path.lower().endswith(SUPPORTED_EXTENSIONS)
        and path != last_song
    ]


    if not valid_tracks:
        # If the only valid track is the last one, just play it
        valid_tracks = [
            (path, volume, fade)
            for path, volume, fade in tracks
            if os.path.isfile(path) and path.lower().endswith(SUPPORTED_EXTENSIONS)
        ]

    if not valid_tracks:
        print(f"No valid audio files found for key '{key_id}'")
        return

    song_path, volume, fade_in_ms = random.choice(valid_tracks)
    LAST_SONG[key_id] = song_path

    try:
        pygame.mixer.music.load(song_path)
        pygame.mixer.music.set_volume(volume)

        # loop forever if loop=True, otherwise play once
        loops = -1 if loop else 0
        pygame.mixer.music.play(loops=loops, fade_ms=fade_in_ms)

        loop_status = "looping" if loop else "one-shot"
        fade_status = f"fade-in {fade_in_ms}ms" if fade_in_ms > 0 else "no fade"

        print(
            f"▶ Playing: {os.path.basename(song_path)} "
            f"({loop_status}, vol={volume}, {fade_status})"
        )

    except Exception as e:
        print(f"Error playing {song_path}: {e}")

def stop_song():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
        print("⏹ Song stopped")
    else:
        print("No song is currently playing")

# Bind keys dynamically
for key, files in KEY_BINDINGS.items():
    keyboard.add_hotkey(key, play_random_song, args=(files, key))

keyboard.add_hotkey(STOP_KEY, stop_song)

print("Music hotkeys:")
for key, binding in KEY_BINDINGS.items():
    mode = "loop" if binding["loop"] else "one-shot"
    print(f"  {key} → {len(binding['tracks'])} tracks ({mode})")

print(f"\n{STOP_KEY} → stop song")
print(f"{QUIT_KEY} → quit")

keyboard.wait(QUIT_KEY)
pygame.mixer.music.stop()
