import os
from .archive_files import archive_files

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

def comfyui_archive_output_startup():
    """Registers the archive function in ComfyUI"""
    print("📂 Archive Output Extension Loaded")

WEB_DIRECTORY = "./web"

# Expose the archive function so JavaScript can trigger it
def execute_archive():
    """Function triggered by JavaScript button"""
    message = archive_files()
    print(f"✅ Archive Output: {message}")
    return message
