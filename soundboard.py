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
    "*": {
        "loop": True,
        "name": "Radio Tuning",
        "tracks": [
            (r"Music\Radio Tuning\Rolling-Radio-Dial_LoFi.mp3", 1, 1000),
        ],
    },
    "1": {
        "loop": False,
        "name": "Set Open",
        "tracks": [
            (r"Music\Set Open\Trouble-on-Mercury_Looping.mp3", 1, 1000),
        ],
    },
    "2": {
        "loop": True,
        "name": "Orchestral",
        "tracks": [
            (r"Music\Orchestral\711018__muyo5438__atmosphere-music-for-nature-movies.mp3", 1, 1000),
            (r"Music\Orchestral\789277__matio888__cinematic-strings-and-piano.mp3", 1, 1000),
            (r"Music\Orchestral\824902__feres12__emotional_strings.mp3", 1, 1000),
        ],
    },
    "3": {
        "loop": True,
        "name": "Industrial Ambience",
        "tracks": [
            (r"Music\Industrial Ambience\Factory-On-Mercury_Looping.mp3", 1, 1000),
            (r"Music\Industrial Ambience\Security-Breach_Looping.mp3", 1, 1000),
            (r"Music\Industrial Ambience\788422__nielsvdb__nightsky-drone.wav", 1, 1000),
        ],
    },
    "4": {
        "loop": True,
        "name": "Peaceful",
        "tracks": [
            (r"Music\Peaceful\Digital-Dew-Drops_v001.mp3", 1, 1000),
        ],
    },
    "5": {
        "loop": True,
        "name": "Choral",
        "tracks": [
            (r"Music\Choral\811110__sondredrakensson__touchstone-vocals-only.wav", 1, 1000),
            (r"Music\Choral\830549__sondredrakensson__verdandi-choral-mix.wav", 1, 1000),
        ],
    },
    "6": {
        "loop": True,
        "name": "Action",
        "tracks": [
            (r"Music\Action\Sector-Off-Limits_Looping.mp3", 1, 1000),
            (r"Music\Action\Steamtech-Mayhem_Looping.mp3", 1, 1000),
            (r"Music\Action\World-of-Automatons_Looping_v001.mp3", 1, 1000),
        ],
    },
    "7": {
        "loop": True,
        "name": "Space Ambience",
        "tracks": [
            (r"Music\Space Ambience\Blazing-Stars_Looping.mp3", 0.7, 1000),
            (r"Music\Space Ambience\Retro-Sci-Fi-Planet_Looping.mp3", 1, 1000),
            (r"Music\Space Ambience\786225__freewheeel__post-apo-music.wav", 1, 1000),
        ],
    },
    "8": {
        "loop": True,
        "name": "Suspense",
        "tracks": [
            (r"Music\Suspense\Cold-Moon_Looping.mp3", 1, 1000),
            (r"Music\Suspense\Creature-from-the-Dark-Lagoon_Looping.mp3", 1, 1000),
            (r"Music\Suspense\Dizzybot_Looping_Remixed.mp3", 1, 1000),
            (r"Music\Suspense\Eerie-Cyber-World_Looping.mp3", 0.7, 1000),
        ],
    },
    "9": {
        "loop": True,
        "name": "Techno Ambience",
        "tracks": [
            (r"Music\Techno Ambience\Dark-Techno-City_Looping.mp3", 1, 1000),
            (r"Music\Techno Ambience\Night-Winds_Looping.mp3", 1, 1000),
            (r"Music\Techno Ambience\Urban-Jungle-2061_Looping.mp3", 1, 1000),
        ],
    },
}

LAST_SONG = {key: None for key in KEY_BINDINGS}

STOP_KEY = "0"
QUIT_KEY = "esc"

CURRENT_VOLUME = 1.0   # default volume (0.0 - 1.0)
VOLUME_STEP = 0.1      # how much + / - changes volume

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
        global CURRENT_VOLUME
        CURRENT_VOLUME = volume
        pygame.mixer.music.set_volume(CURRENT_VOLUME)

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

def change_volume(delta):
    global CURRENT_VOLUME

    if not pygame.mixer.music.get_busy():
        print("No song playing")
        return

    CURRENT_VOLUME += delta

    # Clamp between 0.0 and 1.0
    CURRENT_VOLUME = max(0.0, min(1.0, CURRENT_VOLUME))

    pygame.mixer.music.set_volume(CURRENT_VOLUME)

    print(f"🔊 Volume set to {round(CURRENT_VOLUME, 2)}")

# Bind keys dynamically
for key, files in KEY_BINDINGS.items():
    keyboard.add_hotkey(key, play_random_song, args=(files, key))

keyboard.add_hotkey(STOP_KEY, stop_song)
keyboard.add_hotkey("+", change_volume, args=(VOLUME_STEP,))
keyboard.add_hotkey("-", change_volume, args=(-VOLUME_STEP,))

print("Music hotkeys:")
for key, binding in KEY_BINDINGS.items():
    print(f"  {key} → {binding["name"]}")

print(f"\n{STOP_KEY} → stop song")
print(f"{QUIT_KEY} → quit")

keyboard.wait(QUIT_KEY)
pygame.mixer.music.stop()
