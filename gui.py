import customtkinter as ctk
import threading
import logging
import sys
import os
import subprocess
from pathlib import Path
from tkinter import filedialog, colorchooser
from main import process_video
from captions.utils import setup_logging

# Configure CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", msg + "\n")
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
        self.text_widget.after(0, append)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YT Faceless Captions")
        self.geometry("900x700")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Create Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.tabview.add("General")
        self.tabview.add("Style")
        
        self.setup_general_tab()
        self.setup_style_tab()

        # Log Output (Bottom)
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)

        self.log_label = ctk.CTkLabel(self.log_frame, text="Logs:")
        self.log_label.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="w")

        self.log_text = ctk.CTkTextbox(self.log_frame, state="disabled")
        self.log_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # Setup Logging
        self.setup_gui_logging()
        
        self.last_output_path = None

    def setup_general_tab(self):
        tab = self.tabview.tab("General")
        tab.grid_columnconfigure(0, weight=1)

        # Input File
        self.input_frame = ctk.CTkFrame(tab)
        self.input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.input_frame, text="Input File:").grid(row=0, column=0, padx=10, pady=10)
        self.input_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Select video or audio file...")
        self.input_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.input_frame, text="Browse", command=self.browse_input).grid(row=0, column=2, padx=10, pady=10)

        # Output File (Optional)
        self.output_frame = ctk.CTkFrame(tab)
        self.output_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.output_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.output_frame, text="Output File:").grid(row=0, column=0, padx=10, pady=10)
        self.output_entry = ctk.CTkEntry(self.output_frame, placeholder_text="Optional (Auto-generated if empty)")
        self.output_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.output_frame, text="Save As", command=self.browse_output).grid(row=0, column=2, padx=10, pady=10)

        # Options Grid
        self.options_frame = ctk.CTkFrame(tab)
        self.options_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.options_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Preset
        ctk.CTkLabel(self.options_frame, text="Preset:").grid(row=0, column=0, padx=10, pady=(10, 0))
        self.preset_option = ctk.CTkOptionMenu(self.options_frame, values=["tiktok", "clean"])
        self.preset_option.grid(row=1, column=0, padx=10, pady=(0, 10))

        # Model
        ctk.CTkLabel(self.options_frame, text="Model Size:").grid(row=0, column=1, padx=10, pady=(10, 0))
        self.model_option = ctk.CTkOptionMenu(self.options_frame, values=["tiny", "base", "small", "medium", "large"])
        self.model_option.set("medium")
        self.model_option.grid(row=1, column=1, padx=10, pady=(0, 10))

        # Device
        ctk.CTkLabel(self.options_frame, text="Device:").grid(row=0, column=2, padx=10, pady=(10, 0))
        self.device_option = ctk.CTkOptionMenu(self.options_frame, values=["auto", "cpu", "cuda"])
        self.device_option.grid(row=1, column=2, padx=10, pady=(0, 10))

        # Checkboxes
        self.dry_run_var = ctk.BooleanVar(value=False)
        self.dry_run_check = ctk.CTkCheckBox(tab, text="Dry Run (No Burn-in)", variable=self.dry_run_var)
        self.dry_run_check.grid(row=3, column=0, padx=20, pady=10)

        # Action Buttons
        self.action_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.action_frame.grid(row=4, column=0, padx=10, pady=20, sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)
        self.action_frame.grid_columnconfigure(1, weight=1)

        self.start_btn = ctk.CTkButton(self.action_frame, text="Start Processing", command=self.start_processing, height=40, font=("Arial", 16, "bold"))
        self.start_btn.grid(row=0, column=0, padx=10, sticky="ew")

        self.open_folder_btn = ctk.CTkButton(self.action_frame, text="Open Output Folder", command=self.open_output_folder, height=40, state="disabled")
        self.open_folder_btn.grid(row=0, column=1, padx=10, sticky="ew")

    def setup_style_tab(self):
        tab = self.tabview.tab("Style")
        tab.grid_columnconfigure(0, weight=1)
        
        # Font Settings
        self.font_frame = ctk.CTkFrame(tab)
        self.font_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.font_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.font_frame, text="Font Family:").grid(row=0, column=0, padx=10, pady=10)
        self.font_entry = ctk.CTkEntry(self.font_frame, placeholder_text="Arial")
        self.font_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.font_frame, text="Font Size:").grid(row=1, column=0, padx=10, pady=10)
        self.font_size_entry = ctk.CTkEntry(self.font_frame, placeholder_text="60")
        self.font_size_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        # Position
        ctk.CTkLabel(self.font_frame, text="Position:").grid(row=2, column=0, padx=10, pady=10)
        self.position_option = ctk.CTkOptionMenu(self.font_frame, values=["Bottom", "Middle", "Top"])
        self.position_option.set("Bottom")
        self.position_option.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # Colors
        self.color_frame = ctk.CTkFrame(tab)
        self.color_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.color_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Helper to create color row
        def create_color_row(row, label_text, attr_name):
            ctk.CTkLabel(self.color_frame, text=label_text).grid(row=row, column=0, padx=10, pady=10, sticky="w")
            
            # Entry to show hex code
            entry = ctk.CTkEntry(self.color_frame, width=100)
            entry.grid(row=row, column=1, padx=10, pady=10)
            setattr(self, f"{attr_name}_entry", entry)
            
            # Button to pick
            btn = ctk.CTkButton(self.color_frame, text="Pick", width=60, 
                                command=lambda: self.pick_color(getattr(self, f"{attr_name}_entry")))
            btn.grid(row=row, column=2, padx=10, pady=10)

        create_color_row(0, "Text Color:", "text_color")
        create_color_row(1, "Highlight Box Color:", "highlight_color")
        create_color_row(2, "Highlight Text Color:", "highlight_text_color")
        create_color_row(3, "Outline Color:", "outline_color")

    def pick_color(self, entry_widget):
        color = colorchooser.askcolor(title="Choose Color")
        if color[1]: # Hex code
            entry_widget.delete(0, "end")
            entry_widget.insert(0, color[1])

    def setup_gui_logging(self):
        handler = TextHandler(self.log_text)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

    def browse_input(self):
        filename = filedialog.askopenfilename(filetypes=[("Video/Audio", "*.mp4 *.mp3 *.wav *.m4a *.mkv *.mov")])
        if filename:
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, filename)

    def browse_output(self):
        filename = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 Video", "*.mp4")])
        if filename:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, filename)

    def open_output_folder(self):
        if self.last_output_path and os.path.exists(self.last_output_path):
            folder = os.path.dirname(self.last_output_path)
            if os.name == 'nt':
                os.startfile(folder)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', folder])
            else:
                subprocess.Popen(['xdg-open', folder])

    def hex_to_ass(self, hex_color):
        """Converts #RRGGBB to &H00BBGGRR"""
        if not hex_color or not hex_color.startswith("#"):
            return None
        r = hex_color[1:3]
        g = hex_color[3:5]
        b = hex_color[5:7]
        return f"&H00{b}{g}{r}".upper()

    def start_processing(self):
        input_file = self.input_entry.get()
        if not input_file:
            self.log("Error: Please select an input file.")
            return

        output_file = self.output_entry.get()
        if not output_file:
            output_file = None

        preset = self.preset_option.get()
        model = self.model_option.get()
        device = self.device_option.get()
        dry_run = self.dry_run_var.get()

        # Gather Style Overrides
        style_options = {}
        
        font_name = self.font_entry.get()
        if font_name: style_options['font_name'] = font_name
        
        font_size = self.font_size_entry.get()
        if font_size: style_options['font_size'] = font_size
        
        position = self.position_option.get()
        if position: style_options['position'] = position.lower()
        
        text_color = self.text_color_entry.get()
        if text_color: style_options['color'] = self.hex_to_ass(text_color)
        
        highlight_color = self.highlight_color_entry.get()
        if highlight_color: style_options['highlight_color'] = self.hex_to_ass(highlight_color)
        
        highlight_text_color = self.highlight_text_color_entry.get()
        if highlight_text_color: style_options['highlight_text_color'] = self.hex_to_ass(highlight_text_color)
        
        outline_color = self.outline_color_entry.get()
        if outline_color: style_options['outline_color'] = self.hex_to_ass(outline_color)

        self.start_btn.configure(state="disabled", text="Processing...")
        self.open_folder_btn.configure(state="disabled")
        self.input_entry.configure(state="disabled")
        
        thread = threading.Thread(target=self.run_process, args=(input_file, output_file, preset, model, device, dry_run, style_options))
        thread.start()

    def run_process(self, input_file, output_file, preset, model, device, dry_run, style_options):
        try:
            # We need to know the output path to enable the button later
            # If output_file is None, main.py generates it.
            # We can guess it or modify main.py to return it.
            # For now, let's rely on the fact that if output_file is None, it's input_file + _out.mp4
            
            process_video(
                input_file=input_file,
                output_file=output_file,
                preset=preset,
                model=model,
                device=device,
                dry_run=dry_run,
                style_options=style_options
            )
            
            # Determine output path for the button
            if output_file:
                self.last_output_path = output_file
            else:
                # Replicate logic from utils.py roughly
                p = Path(input_file)
                self.last_output_path = str(p.with_name(f"{p.stem}_out.mp4"))

            self.log("Processing Complete!")
            self.after(0, lambda: self.open_folder_btn.configure(state="normal"))
            
        except Exception as e:
            self.log(f"Error: {e}")
        finally:
            self.after(0, self.reset_ui)

    def reset_ui(self):
        self.start_btn.configure(state="normal", text="Start Processing")
        self.input_entry.configure(state="normal")

    def log(self, message):
        logging.info(message)

if __name__ == "__main__":
    app = App()
    app.mainloop()
