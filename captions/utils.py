import logging
import shutil
import sys
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def setup_logging():
    """Configures logging with colored output."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def log_info(message: str):
    """Logs an info message in blue."""
    logging.info(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {message}")

def log_success(message: str):
    """Logs a success message in green."""
    logging.info(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {message}")

def log_warning(message: str):
    """Logs a warning message in yellow."""
    logging.warning(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {message}")

def log_error(message: str):
    """Logs an error message in red."""
    logging.error(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {message}")

def check_ffmpeg():
    """Checks if ffmpeg is installed and available on PATH."""
    if not shutil.which("ffmpeg"):
        log_error("FFmpeg not found on PATH. Please install FFmpeg and try again.")
        sys.exit(1)
    log_info("FFmpeg found.")

def get_output_path(input_path: str, output_path: str = None, extension: str = ".mp4") -> Path:
    """Determines the output path based on input path if not provided."""
    input_p = Path(input_path)
    if output_path:
        return Path(output_path)
    return input_p.with_name(f"{input_p.stem}_out{extension}")
