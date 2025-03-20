import os
import sys

# Ensure ComfyUI Manager can detect this package
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Load the archive API when ComfyUI starts
from .archive_api import register_api

def comfyui_archive_output_startup(app):
    register_api(app)

WEB_DIRECTORY = "./web"
