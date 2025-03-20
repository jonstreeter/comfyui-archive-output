import os
import sys

# Ensure ComfyUI detects this custom node
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Load the archive API
from .archive_api import register_api

def comfyui_archive_output_startup(app):
    register_api(app)

# Tell ComfyUI where to find our JavaScript extension
WEB_DIRECTORY = "./web"
