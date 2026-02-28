import random
import pygame
import keyboard
import os
import configparser
import zipfile
import sys
import argparse
import tkinter as tk
from tkinter import ttk, font as tkfont

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

def discover_bindings(music_dir):
    """Scan music_dir and return {key: directory} for subdirs with key= in their config.ini."""
    bindings = {}
    try:
        entries = os.listdir(music_dir)
    except FileNotFoundError:
        return bindings
    for entry in entries:
        path = os.path.join(music_dir, entry)
        if not os.path.isdir(path):
            continue
        cfg = load_dir_config(path)
        key = cfg.defaults().get("key", "").strip()
        if key:
            bindings[key] = path
    return bindings

KEY_BINDINGS = discover_bindings(_music_dir)
PLAYED_TRACKS = {key: set() for key in KEY_BINDINGS}

def get_binding_meta(directory):
    dir_config = load_dir_config(directory)
    defaults = dir_config.defaults()
    name = defaults.get("name", os.path.basename(directory))
    loop = defaults.get("loop", "true").strip().lower() in ("true", "1", "yes")
    return name, loop

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
            if dir_config.getboolean(filename, "suppress", fallback=False):
                continue
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
        ui.set_status(f"No audio files found for key '{key_id}'")
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

        name, _ = get_binding_meta(directory)
        loop_label = "looping" if loop else "one-shot"
        fade_status = f"fade-in {fade_in_ms}ms" if fade_in_ms > 0 else "no fade"
        ui.set_status(f"Playing: {os.path.basename(song_path)}", f"{name}  \u00b7  {loop_label}")
        ui.set_volume(CURRENT_VOLUME)
        print(f"▶ Playing: {os.path.basename(song_path)} ({loop_label}, vol={volume}, {fade_status})")

    except Exception as e:
        ui.set_status(f"Error: {e}")
        print(f"Error playing {song_path}: {e}")

def stop_song():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
        ui.set_status("Stopped")
        print("⏹ Song stopped")
    else:
        ui.set_status("Nothing playing")
        print("No song is currently playing")

def change_volume(delta):
    global CURRENT_VOLUME

    if not pygame.mixer.music.get_busy():
        return

    CURRENT_VOLUME += delta
    CURRENT_VOLUME = max(0.0, min(1.0, CURRENT_VOLUME))
    pygame.mixer.music.set_volume(CURRENT_VOLUME)
    ui.set_volume(CURRENT_VOLUME)
    print(f"Volume set to {round(CURRENT_VOLUME, 2)}")

def quit_app():
    pygame.mixer.music.stop()
    ui.quit()

# ------------------------ #

class SoundboardUI:
    BG      = "#111111"
    FG      = "#ffffff"
    FG_DIM  = "#aaaaaa"
    FG_KEY  = "#60a5fa"  # blue for key numbers
    FG_NOW  = "#4ade80"  # green for now-playing status

    def __init__(self, root, bindings):
        self.root = root
        root.title("Soundboard")
        root.attributes("-topmost", True)
        root.configure(bg=self.BG, padx=48, pady=28)
        root.protocol("WM_DELETE_WINDOW", quit_app)
        root.state("zoomed")  # start maximized

        # --- Hotkeys section (two-column grid) ---
        tk.Label(root, text="HOTKEYS", font=("Segoe UI", 12, "bold"),
                 fg=self.FG_DIM, bg=self.BG).pack(anchor="w")

        bindings_frame = tk.Frame(root, bg=self.BG)
        bindings_frame.pack(anchor="w", pady=(8, 0))

        sorted_bindings = sorted(bindings.items())
        n_rows = (len(sorted_bindings) + 1) // 2  # split into 2 columns
        for i, (key, directory) in enumerate(sorted_bindings):
            col = (i // n_rows) * 3   # each binding occupies 3 grid columns
            row = i % n_rows
            name, _ = get_binding_meta(directory)
            tk.Label(bindings_frame, text=key, font=("Consolas", 36, "bold"),
                     fg=self.FG_KEY, bg=self.BG, width=3, anchor="w"
                     ).grid(row=row, column=col,     sticky="w", padx=(0, 4),  pady=3)
            tk.Label(bindings_frame, text="\u2192", font=("Segoe UI", 28),
                     fg=self.FG_DIM, bg=self.BG
                     ).grid(row=row, column=col + 1, sticky="w", padx=(0, 12), pady=3)
            tk.Label(bindings_frame, text=name, font=("Segoe UI", 32, "bold"),
                     fg=self.FG, bg=self.BG
                     ).grid(row=row, column=col + 2, sticky="w", padx=(0, 64), pady=3)

        tk.Frame(root, bg="#333333", height=2).pack(fill="x", pady=18)

        # --- Now playing section ---
        self._status_font = tkfont.Font(family="Segoe UI", size=32, weight="bold")
        self._status_line1_full = "Idle"
        self.status_line1 = tk.StringVar(value="Idle")
        self.status_line2 = tk.StringVar(value="")
        self._status_label = tk.Label(root, textvariable=self.status_line1,
                 font=self._status_font, fg=self.FG_NOW, bg=self.BG,
                 justify="left", anchor="w")
        self._status_label.pack(anchor="w", fill="x")
        self._status_label.bind("<Configure>", self._update_elided_status)
        tk.Label(root, textvariable=self.status_line2, font=("Segoe UI", 20),
                 fg=self.FG_DIM, bg=self.BG, justify="left").pack(anchor="w")
        self.volume_var = tk.StringVar(value="")
        tk.Label(root, textvariable=self.volume_var, font=("Segoe UI", 18),
                 fg=self.FG_DIM, bg=self.BG).pack(anchor="w", pady=(6, 0))

        tk.Frame(root, bg="#333333", height=2).pack(fill="x", pady=18)

        # --- Controls section ---
        tk.Label(root, text="CONTROLS", font=("Segoe UI", 12, "bold"),
                 fg=self.FG_DIM, bg=self.BG).pack(anchor="w")

        controls_frame = tk.Frame(root, bg=self.BG)
        controls_frame.pack(anchor="w", pady=(6, 0))
        for key, label in [("0", "Stop"), ("Esc", "Quit"), ("+  /  \u2212", "Volume")]:
            row = tk.Frame(controls_frame, bg=self.BG)
            row.pack(anchor="w", pady=2)
            tk.Label(row, text=key, font=("Consolas", 18),
                     fg=self.FG_DIM, bg=self.BG, width=8, anchor="w").pack(side="left")
            tk.Label(row, text="\u2192", font=("Segoe UI", 18),
                     fg=self.FG_DIM, bg=self.BG).pack(side="left", padx=(4, 12))
            tk.Label(row, text=label, font=("Segoe UI", 18),
                     fg=self.FG_DIM, bg=self.BG).pack(side="left")

    def _update_elided_status(self, event=None):
        full = self._status_line1_full
        width = self._status_label.winfo_width()
        if width <= 1:
            self.status_line1.set(full)
            return
        if self._status_font.measure(full) <= width:
            self.status_line1.set(full)
            return
        text = full
        while text and self._status_font.measure(text + "...") > width:
            text = text[:-1]
        self.status_line1.set(text + "...")

    def set_status(self, line1, line2=""):
        def _update():
            self._status_line1_full = line1
            self._update_elided_status()
            self.status_line2.set(line2)
        self.root.after(0, _update)

    def set_volume(self, vol):
        self.root.after(0, lambda: self.volume_var.set(f"Volume: {round(vol * 100)}%"))

    def quit(self):
        self.root.after(0, self.root.destroy)

# ------------------------ #

root = tk.Tk()
ui = SoundboardUI(root, KEY_BINDINGS)

for key, directory in KEY_BINDINGS.items():
    keyboard.add_hotkey(key, play_random_song, args=(directory, key), suppress=True)

keyboard.add_hotkey(STOP_KEY, stop_song, suppress=True)
keyboard.add_hotkey(QUIT_KEY, quit_app, suppress=True)
keyboard.add_hotkey("+", change_volume, args=(VOLUME_STEP,), suppress=True)
keyboard.add_hotkey("-", change_volume, args=(-VOLUME_STEP,), suppress=True)

root.mainloop()
pygame.mixer.music.stop()
