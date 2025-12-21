import PyInstaller.__main__
import shutil
from pathlib import Path

def build():
    # Define the main script
    main_script = "gui.py"
    app_name = "YtFacelessCaptions"

    # Clean previous build
    if Path("dist").exists():
        shutil.rmtree("dist")
    if Path("build").exists():
        shutil.rmtree("build")

    # PyInstaller arguments
    args = [
        main_script,
        "--name", app_name,
        "--onefile",  # Create a single executable
        "--windowed", # No console window
        "--add-data", "presets;presets", # Include presets folder
        "--collect-all", "faster_whisper", # Collect faster-whisper dependencies
        "--collect-all", "ctranslate2",    # Collect ctranslate2 dependencies
        "--clean",
        "--noconfirm",
    ]

    print(f"Building {app_name}...")
    PyInstaller.__main__.run(args)
    print("Build complete!")

if __name__ == "__main__":
    build()
