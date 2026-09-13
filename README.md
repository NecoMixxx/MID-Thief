# MID-Thief (CLI Edition)

High-performance, cross-platform CLI MIDI player and synthesis engine built with Python, `mido`, and `pyfluidsynth`. Features dynamic SoundFont (`.sf2`/`.sf3`) swapping, cassette-style seek scrubbing, non-blocking multithreaded playback, native Windows context menu integration, and offline WAV rendering.

---

## Quick Start

1. **Install Context Menu (Windows Optional):** Run `MID-Thief.bat install` or type `install` in the app.
2. **Add SoundFonts:** Place `.sf2` files into `Sound Fonts/` or right-click any `.sf2` file -> **Import SoundFont to MID-Thief**.
3. **Add MIDI:** Place `.mid` files into `Tracks_MIDI/` or right-click any `.mid` file -> **Import to MID-Thief**.
4. **Run Application:** Double-click `MID-Thief.bat` or run `python MID-Thief.py [optional_track.mid]`.
5. **Basic Commands:**
   - `load track_name` : Load track from `Tracks_MIDI/` (omit `.mid`)
   - `start` : Begin playback in background
   - `sf bank_name/number` : Switch active SoundFont instantly
   - `seek 45` : Jump to 45s with cassette scrubbing
   - `export out.wav` : Open file dialog and render loaded track to WAV
   - `break` : Exit application safely

---

## System Requirements & Dependencies

- **Python:** 3.8+
- **Python packages:** `mido`, `pyfluidsynth`
- **System libraries:**
  - **Windows:** Pre-bundled DLLs included in root directory (`libfluidsynth-3.dll`, `SDL3.dll`, `sndfile.dll`).
  - **macOS:** `brew install fluidsynth`
  - **Linux:** `sudo apt install fluidsynth libasound2-dev`

---

## What is New in v2.1

- **Windows Context Menu Integration:** Right-click `.mid`, `.midi`, `.sf2`, or `.sf3` files to import or export instantly.
- **One-Click Installation:** Integrated `install` and `uninstall` commands directly into `MID-Thief.bat` and the Python CLI shell.
- **Interactive File Exporting:** WAV export triggers native Windows file dialogs to choose output paths and custom filenames.
- **CLI Argument Handlers:** Full flag support (`--import`, `--export`, `--sf2`) for external automation and launcher integration.
- **Direct Audio Synthesis:** FluidSynth engine real-time processing (replaced external MIDI virtual ports).
- **Cassette-Style Seeking:** Fast-forward and rewind audio scrubbing FX during timestamp jumps.

---

## Features

- Windows Shell Integration for instant file processing via Right-Click menu.
- Real-Time SoundFont Synthesis using standard `.sf2` / `.sf3` banks.
- Drag-and-drop support directly into terminal or via Windows Explorer.
- Fast-forward/rewind cassette scrubbing audio effects.
- Native OS save file dialogs for WAV exports with optional 2s reverb tail.
- Dynamic channel controller volume sync (CC 7).

---

## Folder Structure

```text
.
├── .venv/               # Python virtual environment
├── Sound Fonts/         # Place .sf2 / .sf3 soundbank files here
├── Tracks_MIDI/         # Place input .mid files here
├── .gitattributes       # Git LFS config for audio assets
├── libfluidsynth-3.dll  # FluidSynth core library
├── libfluidsynth.dll    # FluidSynth binding DLL
├── MID-Thief.bat        # Windows CLI Launcher & Registry Installer
├── MID-Thief.py         # Main Python application
├── README.md            # Project documentation
├── SDL3.dll             # Audio output driver dependency
└── sndfile.dll          # Audio file rendering library