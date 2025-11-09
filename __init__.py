"""
ComfyUI Archive Output Extension
Adds an archive button to the ComfyUI interface for archiving output files.
"""

import os
from server import PromptServer
from .archive_api import setup_routes as setup_archive_routes
from .compress_api import setup_routes as setup_compress_routes

# Optional: Keep the workflow node for backward compatibility
from .archive_workflow_node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# Register web directory for UI extension
WEB_DIRECTORY = "./web"

# Setup API routes
routes = PromptServer.instance.routes
setup_archive_routes(routes)
setup_compress_routes(routes)

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

print("[ComfyUI] Loaded: Archive Output Extension with Compression")
print("[ComfyUI] Archive Output: Archive API routes registered")
print("[ComfyUI] Archive Output: Compression API routes registered")
print("[ComfyUI] Archive Output: Web extension loaded from:", WEB_DIRECTORY)
