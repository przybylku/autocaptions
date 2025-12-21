import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any
from faster_whisper import WhisperModel
from .utils import log_info, log_success, log_error, log_warning

class Word:
    def __init__(self, word: str, start: float, end: float, probability: float):
        self.word = word.strip()
        self.start = start
        self.end = end
        self.probability = probability

    def to_dict(self) -> Dict[str, Any]:
        return {
            "word": self.word,
            "start": self.start,
            "end": self.end,
            "probability": self.probability
        }

def extract_audio(video_path: Path, output_path: Path) -> Path:
    """Extracts audio from video using ffmpeg."""
    log_info(f"Extracting audio from {video_path}...")
    
    # -y overwrite, -vn no video, -ac 1 mono, -ar 16000 sample rate
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log_success(f"Audio extracted to {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        log_error(f"FFmpeg failed: {e.stderr.decode()}")
        raise


def transcribe(audio_path: Path, model_size: str = "medium", device: str = "auto", compute_type: str = "default") -> List[Word]:
    """Transcribes audio using faster-whisper and returns a list of words."""
    
    def _run_transcription(dev, comp_type):
        log_info(f"Loading Whisper model ({model_size}) on {dev}...")
        model = WhisperModel(model_size, device=dev, compute_type=comp_type)
        log_info("Transcribing...")
        segments, info = model.transcribe(str(audio_path), word_timestamps=True)
        
        words = []
        for segment in segments:
            if segment.words:
                for w in segment.words:
                    words.append(Word(w.word, w.start, w.end, w.probability))
        return words

    try:
        return _run_transcription(device, compute_type)
    except Exception as e:
        log_warning(f"Transcription failed with device='{device}': {e}")
        if device != "cpu":
            log_info("Attempting fallback to CPU...")
            try:
                # int8 is usually safe and fast enough for CPU
                return _run_transcription("cpu", "int8")
            except Exception as e2:
                log_error(f"Failed to transcribe on CPU: {e2}")
                raise e2
        else:
            raise

def save_transcript(words: List[Word], output_path: Path):
    """Saves the transcript to a JSON file."""
    data = [w.to_dict() for w in words]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log_info(f"Transcript saved to {output_path}")
