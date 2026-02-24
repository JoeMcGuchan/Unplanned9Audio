import random
import pygame
import keyboard
import os
import configparser
import zipfile
import sys
import argparse

sys.stdout.reconfigure(encoding='utf-8')

# -------- UNPACK MUSIC ZIP -------- #
_script_dir = os.path.dirname(os.path.abspath(__file__))
_music_dir = os.path.join(_script_dir, "Music")

_parser = argparse.ArgumentParser(description="Music soundboard")
_parser.add_argument("zip_file", nargs="?", default=os.path.join(_script_dir, "music.zip"),
                     help="Path to music zip file (default: music.zip)")
_args = _parser.parse_args()

_zip_path = _args.zip_file

if os.path.isfile(_zip_path) and not os.path.isdir(_music_dir):
    print(f"Music folder not found — unpacking {_zip_path}...")
    with zipfile.ZipFile(_zip_path, "r") as _zf:
        _zf.extractall(_script_dir)
    print("Music unpacked.")

# ---------------------------------- #

pygame.mixer.init()

SUPPORTED_EXTENSIONS = (".mp3", ".wav", ".ogg", ".flac")

DEFAULT_VOLUME = 1.0
DEFAULT_FADE_MS = 1000

# -------- CONFIG -------- #

# Maps hotkey -> Music subdirectory. name and loop are read from each directory's config.ini.
KEY_BINDINGS = {
    "*": r"Music\Radio Tuning",
    "1": r"Music\Set Open",
    "2": r"Music\Orchestral",
    "3": r"Music\Industrial Ambience",
    "4": r"Music\Peaceful",
    "5": r"Music\Choral",
    "6": r"Music\Action",
    "7": r"Music\Space Ambience",
    "8": r"Music\Suspense",
    "9": r"Music\Techno Ambience",
}

PLAYED_TRACKS = {key: set() for key in KEY_BINDINGS}

def get_binding_meta(directory):
    dir_config = load_dir_config(directory)
    defaults = dir_config.defaults()
    name = defaults.get("name", os.path.basename(directory))
    loop = defaults.get("loop", "true").strip().lower() in ("true", "1", "yes")
    return name, loop

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

def play_random_song(directory, key_id):
    dir_config = load_dir_config(directory)
    _, loop = get_binding_meta(directory)
    tracks = get_tracks_from_directory(directory, dir_config)

    if not tracks:
        print(f"No valid audio files found for key '{key_id}'")
        return

    # Pick from tracks not yet played this cycle
    unplayed = [(p, v, f) for p, v, f in tracks if p not in PLAYED_TRACKS[key_id]]
    if not unplayed:
        # All tracks played — reset and start a new cycle
        PLAYED_TRACKS[key_id] = set()
        unplayed = tracks

    song_path, volume, fade_in_ms = random.choice(unplayed)
    PLAYED_TRACKS[key_id].add(song_path)

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
for key, directory in KEY_BINDINGS.items():
    keyboard.add_hotkey(key, play_random_song, args=(directory, key), suppress=True)

keyboard.add_hotkey(STOP_KEY, stop_song, suppress=True)
keyboard.add_hotkey("+", change_volume, args=(VOLUME_STEP,), suppress=True)
keyboard.add_hotkey("-", change_volume, args=(-VOLUME_STEP,), suppress=True)

print("Music hotkeys:")
for key, directory in KEY_BINDINGS.items():
    name, _ = get_binding_meta(directory)
    print(f"  {key} → {name}")

print(f"\n{STOP_KEY} → stop song")
print(f"{QUIT_KEY} → quit")

keyboard.wait(QUIT_KEY)
pygame.mixer.music.stop()
