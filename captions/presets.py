import json
import sys
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import yaml

class FontConfig(BaseModel):
    name: str = "Arial"
    size: int = 60
    color: str = "&H00FFFFFF"  # ASS color format (BBGGRR)
    outline_color: str = "&H00000000"
    outline_width: float = 2.0
    shadow_depth: float = 0.0

class HighlightConfig(BaseModel):
    enabled: bool = True
    color: str = "&H0000FFFF"  # Yellow-ish (BBGGRR) -> Yellow is 00FFFF
    opacity: str = "&H00" # Hex opacity (00 is opaque, FF is transparent) - wait, ASS alpha is &H<AA>
    # Actually, for ASS color codes with alpha it is &HAABBGGRR.
    # But usually we set alpha separately or as part of the color string.
    # Let's assume standard ASS color &HBBGGRR and use \alpha or \1a tags if needed.
    # For simplicity, let's stick to &HAABBGGRR if the user provides it, or just &HBBGGRR.
    # We will handle the "box" color.
    
    # For the "Thick Border" trick:
    # The highlight color will be the border color of the highlighted word.
    # So we need a color that looks good as a background box.
    # Yellow: Blue=00, Green=FF, Red=FF -> &H00FFFF
    
    text_color: str = "&H00FFFFFF" # Text color when highlighted (usually white)
    outline_color: str = "&H0000FFFF" # The "box" color (thick outline)
    outline_width: float = 40.0 # Thick border to simulate box
    animation: str = "pop" # "pop", "none"

class ChunkingConfig(BaseModel):
    max_chars: int = 20
    max_words: int = 5
    max_lines: int = 2
    gap_threshold: float = 0.5 # Seconds to force a new segment

class PresetConfig(BaseModel):
    font: FontConfig = Field(default_factory=FontConfig)
    highlight: HighlightConfig = Field(default_factory=HighlightConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    margin_bottom: int = 150
    clean_fillers: bool = False

def load_preset(name_or_path: str) -> PresetConfig:
    """Loads a preset from a name (in presets/) or a file path."""
    
    # Check if it's a file path
    path = Path(name_or_path)
    if not path.exists():
        # Check if it's a preset name in the presets dir
        # Handle PyInstaller _MEIPASS
        if hasattr(sys, '_MEIPASS'):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(__file__).parent.parent
            
        preset_dir = base_dir / "presets"
        path = preset_dir / f"{name_or_path}.json"
        
        if not path.exists():
             # Try adding .json
            path = Path(name_or_path)
            if not path.suffix:
                path = path.with_suffix(".json")
            
            if not path.exists():
                raise FileNotFoundError(f"Preset '{name_or_path}' not found.")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return PresetConfig(**data)
