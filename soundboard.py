import random
import pygame
import keyboard
import os
import configparser
import zipfile

# -------- UNPACK MUSIC ZIP -------- #
_script_dir = os.path.dirname(os.path.abspath(__file__))
_zip_path = os.path.join(_script_dir, "music.zip")
_music_dir = os.path.join(_script_dir, "Music")

if os.path.isfile(_zip_path) and not os.path.isdir(_music_dir):
    print("Music folder not found — unpacking music.zip...")
    with zipfile.ZipFile(_zip_path, "r") as _zf:
        _zf.extractall(_script_dir)
    print("Music unpacked.")

# ---------------------------------- #

pygame.mixer.init()

SUPPORTED_EXTENSIONS = (".mp3", ".wav", ".ogg", ".flac")

DEFAULT_VOLUME = 1.0
DEFAULT_FADE_MS = 1000

# -------- CONFIG -------- #

# loop: whether or not the music should loop on finishing
# directory: path to the folder containing tracks for this key
KEY_BINDINGS = {
    "*": {"loop": True,  "name": "Radio Tuning",       "directory": r"Music\Radio Tuning"},
    "1": {"loop": False, "name": "Set Open",            "directory": r"Music\Set Open"},
    "2": {"loop": True,  "name": "Orchestral",          "directory": r"Music\Orchestral"},
    "3": {"loop": True,  "name": "Industrial Ambience", "directory": r"Music\Industrial Ambience"},
    "4": {"loop": True,  "name": "Peaceful",            "directory": r"Music\Peaceful"},
    "5": {"loop": True,  "name": "Choral",              "directory": r"Music\Choral"},
    "6": {"loop": True,  "name": "Action",              "directory": r"Music\Action"},
    "7": {"loop": True,  "name": "Space Ambience",      "directory": r"Music\Space Ambience"},
    "8": {"loop": True,  "name": "Suspense",            "directory": r"Music\Suspense"},
    "9": {"loop": True,  "name": "Techno Ambience",     "directory": r"Music\Techno Ambience"},
}

LAST_SONG = {key: None for key in KEY_BINDINGS}

STOP_KEY = "0"
QUIT_KEY = "esc"

CURRENT_VOLUME = 1.0   # default volume (0.0 - 1.0)
VOLUME_STEP = 0.1      # how much + / - changes volume

# ------------------------ #

def load_dir_config(directory):
    config = configparser.ConfigParser()
    config_path = os.path.join(directory, "config.ini")
    if os.path.isfile(config_path):
        config.read(config_path)
    return config

def get_tracks_from_directory(directory, dir_config):
    defaults = dir_config.defaults()
    default_volume = float(defaults.get("volume", DEFAULT_VOLUME))
    default_fade = int(defaults.get("fade_in_ms", DEFAULT_FADE_MS))

    tracks = []
    try:
        filenames = os.listdir(directory)
    except FileNotFoundError:
        return tracks

    for filename in filenames:
        if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
            continue
        path = os.path.join(directory, filename)
        if not os.path.isfile(path):
            continue
        if dir_config.has_section(filename):
            volume = dir_config.getfloat(filename, "volume", fallback=default_volume)
            fade = dir_config.getint(filename, "fade_in_ms", fallback=default_fade)
        else:
            volume = default_volume
            fade = default_fade
        tracks.append((path, volume, fade))

    return tracks

def play_random_song(binding, key_id):
    directory = binding["directory"]
    loop = binding["loop"]
    last_song = LAST_SONG[key_id]

    dir_config = load_dir_config(directory)
    tracks = get_tracks_from_directory(directory, dir_config)

    # Prefer a track that wasn't the last one played
    valid_tracks = [(p, v, f) for p, v, f in tracks if p != last_song]
    if not valid_tracks:
        # Only one track available, just replay it
        valid_tracks = tracks

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
    print(f"  {key} → {binding['name']}")

print(f"\n{STOP_KEY} → stop song")
print(f"{QUIT_KEY} → quit")

keyboard.wait(QUIT_KEY)
pygame.mixer.music.stop()
