# Unplanned9Audio

A keyboard-driven music soundboard. Each key triggers a random track from a configured directory, cycling through all tracks before repeating any.

## Usage

```
python soundboard.py [path/to/music.zip]
```

If the `Music` folder doesn't exist and a zip file is present (default: `music.zip` next to the script), it will be unpacked automatically.

## Controls

| Key | Action |
|-----|--------|
| Configured hotkey | Play a random track from that directory |
| `0` | Stop playback |
| `+` / `-` | Increase / decrease volume |
| `Esc` | Quit |

All hotkeys are suppressed — they won't be passed to other applications while the script is running.

## Music directory structure

```
Music/
  My Category/
    config.ini
    track1.mp3
    track2.mp3
    ...
  Another Category/
    config.ini
    ...
```

Supported audio formats: `.mp3`, `.wav`, `.ogg`, `.flac`

Directories without a `config.ini` (or without a `key` set in it) are ignored.

### config.ini

Each subdirectory can have a `config.ini` that controls its behaviour. All fields are optional.

#### [DEFAULT] — directory-wide settings

| Field | Default | Description |
|-------|---------|-------------|
| `key` | *(none)* | Hotkey that triggers this directory. Omit to leave the directory unbound. |
| `name` | directory name | Display name shown at startup. |
| `loop` | `true` | Whether to loop the track continuously (`true`) or play it once (`false`). |
| `volume` | `1.0` | Playback volume from `0.0` to `1.0`. |
| `fade_in_ms` | `1000` | Fade-in duration in milliseconds. Set to `0` for no fade. |

**Example:**

```ini
[DEFAULT]
key = 1
name = Set Open
loop = false
volume = 1.0
fade_in_ms = 1000
```

#### Per-track sections — override settings for individual files

Add a section named after the filename to override any `[DEFAULT]` value for that track, or to suppress it entirely.

| Field | Default | Description |
|-------|---------|-------------|
| `volume` | inherited | Per-track volume override. |
| `fade_in_ms` | inherited | Per-track fade-in override. |
| `suppress` | `false` | Set to `true` to exclude this track from playback. |

**Example:**

```ini
[DEFAULT]
key = 2
name = Orchestral
loop = true
volume = 1.0
fade_in_ms = 1000

[quiet-intro_Looping.mp3]
volume = 0.6

[unwanted-track_Looping.mp3]
suppress = true
```

### Playback order

Tracks are played in random order. No track will repeat until every non-suppressed track in the directory has been played once, at which point the cycle resets.
