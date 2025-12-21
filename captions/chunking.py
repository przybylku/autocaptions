from typing import List
from .asr import Word
from .presets import ChunkingConfig

class CaptionSegment:
    def __init__(self, words: List[Word]):
        self.words = words
        self.start = words[0].start if words else 0.0
        self.end = words[-1].end if words else 0.0
        self.text = " ".join([w.word for w in words])

    def update_times(self):
        if self.words:
            self.start = self.words[0].start
            self.end = self.words[-1].end
            self.text = " ".join([w.word for w in self.words])

def is_punctuation(char: str) -> bool:
    return char in ".?!,;:"

def chunk_words(words: List[Word], config: ChunkingConfig) -> List[CaptionSegment]:
    """Groups words into caption segments based on constraints."""
    segments = []
    current_words = []
    
    for i, word in enumerate(words):
        current_words.append(word)
        
        # Check constraints
        current_text = " ".join([w.word for w in current_words])
        char_count = len(current_text)
        word_count = len(current_words)
        
        # Look ahead for punctuation or gap
        is_last_word = (i == len(words) - 1)
        has_punctuation = is_punctuation(word.word[-1]) if word.word else False
        
        # Time gap check
        next_word_start = words[i+1].start if not is_last_word else word.end
        time_gap = next_word_start - word.end
        
        should_split = False
        
        # Hard limits
        if char_count >= config.max_chars:
            should_split = True
        elif word_count >= config.max_words:
            should_split = True
        elif time_gap > config.gap_threshold:
            should_split = True
        elif has_punctuation:
            # Prefer splitting after punctuation if we have enough content
            # But don't split if it's just one short word unless it's a long pause
            if word_count > 1 or char_count > 5:
                should_split = True
        
        if should_split or is_last_word:
            segments.append(CaptionSegment(current_words))
            current_words = []
            
    return segments
