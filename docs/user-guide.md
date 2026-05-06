# PUtils User Guide

## Requirements

- Python 3.10 or newer.
- Tkinter support.
- `ffmpeg` installed and available on `PATH` for video processing.

Check ffmpeg:

```bash
ffmpeg -version
```

## Start The Tool

From the project directory:

```bash
python -m putils
```

The default interface language is Chinese. Use the language button in the top-right corner to switch between Chinese and English.

## Dependency Status

The top panel shows dependency status reported by each plugin.

For the video saturation plugin, the required dependency is:

- `ffmpeg`

Click `Check` to refresh dependency status. If `ffmpeg` is missing, install it and make sure it is available on `PATH`.

## Adjust Video Saturation

1. Open the `Video Saturation` tab.
2. Set `Saturation ratio`.
   - `1.00` keeps the original saturation.
   - Values below `1.00` reduce saturation.
   - `0.00` produces grayscale-like output.
   - Values above `1.00` increase saturation.
3. Click `Add Videos` and select one or more video files.
4. Optional: choose an output directory with `Browse`.
5. Click `Run`.

The progress bar shows batch processing progress. Each completed or failed file advances the progress count.

If no output directory is selected, each output file is written next to its source video.

Output filenames use this pattern:

```text
original_name_saturation_adjusted.ext
```

Example:

```text
clip.mp4 -> clip_saturation_adjusted.mp4
```

## Operation Logs

The lower panel shows recent operation logs. Logs include:

- Start events.
- Completion events.
- ffmpeg or processing errors.

Click `Refresh` to reload the list immediately. The application also refreshes the panel periodically.

## Stored Data

PUtils stores configuration and logs in separate SQLite databases.

Default locations:

- Windows: `%APPDATA%\PUtils`
- Linux: `$XDG_DATA_HOME/putils` or `~/.local/share/putils`

Files:

- `config.sqlite3`: user settings such as the last selected saturation ratio.
- `logs.sqlite3`: operation logs.
