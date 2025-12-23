import datetime
import tkinter as tk
from tkinter import font as tkfont
from pathlib import Path
from typing import List
from .chunking import CaptionSegment
from .presets import PresetConfig
from .utils import log_info

def format_time(seconds: float) -> str:
    """Formats seconds into ASS timestamp format: H:MM:SS.cc"""
    td = datetime.timedelta(seconds=seconds)
    # Total seconds
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    centis = int((seconds - total_seconds) * 100)
    
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

def get_text_width(text: str, font_family: str, font_size: int) -> int:
    """Calculates the width of text in pixels using tkinter."""
    try:
        # Create a hidden root window if not exists
        try:
            root = tk.Tk()
            root.withdraw()
        except Exception:
            # If Tk is already initialized or fails
            pass
            
        # Use negative size for pixels
        font = tkfont.Font(family=font_family, size=-font_size)
        return font.measure(text)
    except Exception:
        # Fallback estimation if tkinter fails (e.g. headless)
        # Average char width ~0.5 * size? Very rough.
        return int(len(text) * font_size * 0.5)

def generate_ass(segments: List[CaptionSegment], config: PresetConfig, output_path: Path):
    """Generates an ASS subtitle file with word-level highlighting."""
    log_info(f"Generating ASS file at {output_path}...")
    
    # ASS Header
    # Note: HighlightBox uses BorderStyle=3 (Opaque Box)
    # BackColour is the box color.
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{config.font.name},{config.font.size},{config.font.color},&H000000FF,{config.font.outline_color},&H00000000,-1,0,0,0,100,100,0,0,1,{config.font.outline_width},{config.font.shadow_depth},2,10,10,{config.margin_bottom},1
Style: HighlightBox,{config.font.name},{config.font.size},{config.highlight.text_color},&H000000FF,{config.highlight.color},&H00000000,-1,0,0,0,100,100,0,0,3,{config.highlight.padding},0,2,10,10,{config.margin_bottom},1
Style: HighlightText,{config.font.name},{config.font.size},{config.highlight.text_color},&H000000FF,{config.highlight.outline_color},&H00000000,-1,0,0,0,100,100,0,0,1,{config.highlight.outline_width},0,2,10,10,{config.margin_bottom},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    events = []
    
    # Screen center X
    center_x = 1080 // 2
    screen_height = 1920
    
    for seg in segments:
        start_time = format_time(seg.start)
        end_time = format_time(seg.end)
        
        # Calculate positions
        # We need to measure each word and the spaces
        words = seg.words
        word_widths = []
        space_width = get_text_width(" ", config.font.name, config.font.size)
        
        total_width = 0
        for i, w in enumerate(words):
            w_width = get_text_width(w.word, config.font.name, config.font.size)
            word_widths.append(w_width)
            total_width += w_width
            if i < len(words) - 1:
                total_width += space_width
                
        # Starting X position (centered)
        # Alignment 2 is Bottom Center.
        # If we use \pos(x, y), x is the center of the text if alignment is center?
        # No, \pos sets the anchor point.
        # If Alignment=2 (Bottom Center), \pos(x,y) means the bottom-center of the text is at (x,y).
        # So if we want to position words left-to-right, we need to calculate their centers.
        
        # Start X (Left edge of the line)
        start_left_x = center_x - (total_width // 2)
        
        # Y position calculation
        if config.position == "top":
            pos_y = config.margin_bottom # Using margin_bottom as margin_top here
        elif config.position == "middle":
            pos_y = screen_height // 2
        else: # bottom
            pos_y = screen_height - config.margin_bottom
        
        current_x = start_left_x
        
        for i, word in enumerate(words):
            w_width = word_widths[i]
            
            # Calculate center of this word
            word_center_x = current_x + (w_width // 2)
            
            # Base Event (Layer 0) - Default Style
            # We use \pos to position it exactly
            events.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{{\\pos({word_center_x},{pos_y})}}{word.word}")
            
            if config.highlight.enabled:
                # Highlight Event (Layer 1) - HighlightBox Style
                # Only for the duration of the word
                w_start = format_time(word.start)
                w_end = format_time(word.end)
                
                # Animation Tags
                anim_tags = ""
                if hasattr(config.highlight, 'animation') and config.highlight.animation == "pop":
                    # Pop animation: Scale up to 115% quickly
                    anim_tags = "\\fscx115\\fscy115"
                
                # Layer 1: Box (HighlightBox)
                # BorderStyle=3 draws a box around the text.
                # We make the text transparent (\1a&HFF&) so we only see the box.
                events.append(f"Dialogue: 1,{w_start},{w_end},HighlightBox,,0,0,0,,{{\\pos({word_center_x},{pos_y})\\1a&HFF&{anim_tags}}}{word.word}")
                
                # Layer 2: Text (HighlightText)
                # Draws the text face and outline on top of the box.
                events.append(f"Dialogue: 2,{w_start},{w_end},HighlightText,,0,0,0,,{{\\pos({word_center_x},{pos_y}){anim_tags}}}{word.word}")
            
            # Advance X
            current_x += w_width + space_width

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(events))
    
    log_info(f"ASS file generated with {len(events)} events.")
