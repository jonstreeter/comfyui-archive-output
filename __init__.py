import os
from .archive_files import archive_files

# Optional: Remove old frontend integration
WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), 'web')

class ArchiveOutputNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("message",)
    FUNCTION = "archive"

    CATEGORY = "Utilities"

    def archive(self):
        try:
            message = archive_files()
            print(f"✅ Archive Output: {message}")
            return (message,)
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            print(error_msg)
            return (error_msg,)

# Register this node with ComfyUI
NODE_CLASS_MAPPINGS = {
    "ArchiveOutputNode": ArchiveOutputNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArchiveOutputNode": "Archive Output"
}
