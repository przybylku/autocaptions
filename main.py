import argparse
import sys
import subprocess
from pathlib import Path
from captions.utils import setup_logging, log_info, log_error, log_success, log_warning, check_ffmpeg, get_output_path
from captions.presets import load_preset
from captions.asr import extract_audio, transcribe, save_transcript
from captions.chunking import chunk_words
from captions.ass_renderer import generate_ass

def process_video(input_file: str, output_file: str = None, preset: str = "tiktok", 
                  model: str = "medium", device: str = "auto", dry_run: bool = False,
                  style_options: dict = None):
    # 1. Checks
    check_ffmpeg()
    
    input_path = Path(input_file)
    if not input_path.exists():
        log_error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    output_path = get_output_path(input_file, output_file)
    
    # 2. Load Preset
    try:
        config = load_preset(preset)
        log_info(f"Loaded preset: {preset}")
        
        # Apply style overrides
        if style_options:
            log_info("Applying style overrides...")
            if 'font_name' in style_options and style_options['font_name']:
                config.font.name = style_options['font_name']
            if 'font_size' in style_options and style_options['font_size']:
                config.font.size = int(style_options['font_size'])
            if 'color' in style_options and style_options['color']:
                config.font.color = style_options['color']
            if 'outline_color' in style_options and style_options['outline_color']:
                config.font.outline_color = style_options['outline_color']
                config.highlight.outline_color = style_options['outline_color']
            if 'highlight_color' in style_options and style_options['highlight_color']:
                config.highlight.color = style_options['highlight_color']
            if 'highlight_text_color' in style_options and style_options['highlight_text_color']:
                config.highlight.text_color = style_options['highlight_text_color']
            if 'position' in style_options and style_options['position']:
                config.position = style_options['position']
                
    except Exception as e:
        log_error(str(e))
        raise
        
    # 3. Audio Extraction
    temp_audio = input_path.with_suffix(".wav")
    if input_path.suffix.lower() in [".mp3", ".wav", ".m4a"]:
        # Input is audio
        temp_audio = input_path
        log_info("Input is audio file, skipping extraction.")
    else:
        # Input is video
        try:
            extract_audio(input_path, temp_audio)
        except Exception as e:
            raise e
            
    # 4. Transcribe
    try:
        words = transcribe(temp_audio, model_size=model, device=device)
        transcript_path = output_path.with_name(output_path.stem + "_transcript.json")
        save_transcript(words, transcript_path)
    except Exception as e:
        raise e
        
    # 5. Chunking
    segments = chunk_words(words, config.chunking)
    log_info(f"Generated {len(segments)} caption segments.")
    
    # 6. Generate ASS
    ass_path = output_path.with_name(output_path.stem + ".ass")
    generate_ass(segments, config, ass_path)
    
    # 7. Burn-in
    if dry_run:
        log_success("Dry run complete. Artifacts generated.")
        return

    log_info("Burning captions into video...")
    # ffmpeg -i input.mp4 -vf "ass=file.ass" -c:a copy output.mp4
    # Note: We need to re-encode video to burn subtitles.
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vf", f"ass={ass_path.name}",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "copy",
        str(output_path)
    ]
    
    # If input was audio, we can't just burn subs into audio.
    # We would need a background image or video.
    # For this MVP, we assume if input is audio, user might want just the ASS or we fail.
    if input_path.suffix.lower() in [".mp3", ".wav", ".m4a"]:
        log_warning("Input is audio only. Cannot burn subtitles into audio file. ASS file is ready.")
        return

    try:
        # Run ffmpeg in the directory of the ass file to avoid escaping issues with full paths in filter
        subprocess.run(cmd, check=True, cwd=ass_path.parent)
        log_success(f"Video created: {output_path}")
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to burn subtitles: {e}")
        raise e
    finally:
        # Cleanup temp audio if we extracted it
        if input_path.suffix.lower() not in [".mp3", ".wav", ".m4a"] and temp_audio.exists():
            try:
                temp_audio.unlink()
            except:
                pass

def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Generate CapCut-like captions for videos.")
    parser.add_argument("--input", required=True, help="Input video/audio file")
    parser.add_argument("--output", help="Output video file")
    parser.add_argument("--preset", default="tiktok", help="Preset name or path (default: tiktok)")
    parser.add_argument("--dry-run", action="store_true", help="Generate artifacts but do not burn video")
    parser.add_argument("--model", default="medium", help="Whisper model size (tiny, base, small, medium, large)")
    parser.add_argument("--device", default="auto", help="Device for Whisper (auto, cpu, cuda)")
    
    args = parser.parse_args()
    
    try:
        process_video(
            input_file=args.input,
            output_file=args.output,
            preset=args.preset,
            model=args.model,
            device=args.device,
            dry_run=args.dry_run
        )
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    main()
