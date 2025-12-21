# CapCut-Like Captions CLI

A local Python CLI tool to generate viral-style video captions with word-level highlighting (karaoke style), similar to CapCut or TikTok.

## Features
- **Word-level Highlighting**: Highlights the currently spoken word with a background box.
- **Smart Chunking**: Splits captions into readable 1-2 line segments based on natural pauses and constraints.
- **Configurable Presets**: Customize fonts, colors, sizes, and positioning via JSON.
- **Local Processing**: Uses `faster-whisper` for accurate speech-to-text and `ffmpeg` for burning captions locally. No cloud API keys required.

## Prerequisites
- **Python 3.11+**
- **FFmpeg**: Must be installed and added to your system PATH.
  - To verify: run `ffmpeg -version` in your terminal.

## Installation

1. Clone or download this repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage
```bash
python main.py --input video.mp4 --output result.mp4
```

### Using a Preset
```bash
python main.py --input video.mp4 --output result.mp4 --preset tiktok
```

### Dry Run (Generate ASS and Transcript only)
```bash
python main.py --input video.mp4 --dry-run
```

### Options
- `--input`: Path to input video or audio file (required).
- `--output`: Path to output video file (optional, defaults to `input_out.mp4`).
- `--preset`: Name of a preset in `presets/` (e.g., `tiktok`, `clean`) or path to a JSON config file.
- `--model`: Whisper model size (`tiny`, `base`, `small`, `medium`, `large`). Default: `medium`.
- `--device`: Device to run Whisper on (`cpu`, `cuda`, `auto`). Default: `auto`.
- `--dry-run`: Skip the video burning step.

## Configuration (Presets)
You can create your own presets in the `presets/` folder. See `presets/tiktok.json` for an example.

```json
{
    "font": {
        "name": "Arial",
        "size": 70,
        "color": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "outline_width": 3.0
    },
    "highlight": {
        "enabled": true,
        "color": "&H0000FFFF", 
        "text_color": "&H00FFFFFF",
        "outline_width": 40.0
    },
    "chunking": {
        "max_chars": 25,
        "max_words": 6,
        "max_lines": 2
    },
    "margin_bottom": 250
}
```
*Note: Colors are in ASS hex format `&HAABBGGRR` or `&HBBGGRR`.*

## Project Structure
- `main.py`: Entry point.
- `captions/`: Core logic modules.
- `presets/`: Configuration files.
