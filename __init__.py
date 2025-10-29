"""
ComfyUI Archive Output Custom Node
A custom node for archiving ComfyUI output files into date-structured folders.
"""

from .archive_workflow_node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

print("[ComfyUI] Loaded: Archive Output Node")
