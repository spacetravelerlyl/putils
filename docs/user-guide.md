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

The default interface language is Chinese. Open the `配置` / `Settings` tab to switch between Chinese and English.

## Settings

Open the `配置` / `Settings` tab to view and change application settings.

Available settings:

- Interface language.
- Log timezone.
- Database directory.
- Current `config.sqlite3` path.
- Current `logs.sqlite3` path.

Changing the database directory shows a migration button. Use it to copy the current `config.sqlite3` and `logs.sqlite3` files to the target directory. If files with the same names already exist in the target directory, they are backed up before being overwritten.

The new database directory takes effect after restarting the application.

If `PUTILS_DATA_DIR` is set in the environment, it overrides the configured database directory.

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

The colored progress bar shows batch processing progress. Blue means processing, green means all files completed successfully, and red means at least one file failed. Each completed or failed file advances the progress count.

After processing finishes, click `Clear` to remove the current file list and reset the progress display.

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

Log timestamps are stored in UTC and displayed in the timezone selected in Settings. The display format is similar to:

```text
2026-05-06 15:30:00 CST
```

## Stored Data

PUtils stores configuration and logs in separate SQLite databases.

Default locations:

- Windows: `%APPDATA%\PUtils`
- Linux: `$XDG_DATA_HOME/putils` or `~/.local/share/putils`

Files:

- `config.sqlite3`: user settings such as the last selected saturation ratio.
- `logs.sqlite3`: operation logs.
