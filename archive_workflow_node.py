"""
ComfyUI Archive Output Node
Archives files from the output directory into a date-structured archive folder.
"""

import os
import shutil
from datetime import datetime
import folder_paths

try:
    from comfy.utils import interrupt_current_processing
except ImportError:
    interrupt_current_processing = lambda: False


class AnyType(str):
    """
    A special class that allows any type of input to connect to this node.
    This makes the node flexible for workflow integration.
    """
    def __ne__(self, __value: object) -> bool:
        return False


# Wildcard for accepting any input type
any_type = AnyType("*")


class ArchiveOutputWorkflowNode:
    """
    A ComfyUI node that archives files from the output directory into a date-structured
    archive folder, preserving the original subdirectory structure.

    Features:
    - Organizes files by modification date (YYYY-MM-DD)
    - Preserves original folder structure
    - Skips hidden files and specified extensions
    - Cleans up empty directories
    - Supports workflow interruption
    """

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.archive_base_folder = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "trigger": (any_type, {}),
            },
            "optional": {
                "enabled": ("BOOLEAN", {"default": True}),
                "archive_folder_name": ("STRING", {"default": "Archive"}),
                "skip_hidden_files": ("BOOLEAN", {"default": True}),
                "skip_extensions": ("STRING", {
                    "default": ".py,.js,.bat,.sh,.json,.yaml,.yml",
                    "multiline": False
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "execute_archive"
    CATEGORY = "workflow/archiving"
    OUTPUT_NODE = False

    def _ensure_directory_exists(self, path):
        """Create directory if it doesn't exist."""
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
                return True
            except Exception as e:
                print(f"[Archive Node] Error creating directory {path}: {e}")
                return False
        return True

    def _get_file_date_str(self, file_path):
        """Get file modification date as YYYY-MM-DD string."""
        try:
            stat_time = os.path.getmtime(file_path)
            return datetime.fromtimestamp(stat_time).strftime("%Y-%m-%d")
        except Exception as e:
            print(f"[Archive Node] Error getting date for {file_path}: {e}")
            return None

    def _should_skip_file(self, file_name, skip_hidden, skip_ext_list):
        """Determine if a file should be skipped based on rules."""
        if skip_hidden and file_name.startswith("."):
            return True

        if any(file_name.lower().endswith(ext) for ext in skip_ext_list):
            return True

        return False

    def _move_file_to_archive(self, file_path, target_path):
        """Move file to archive location, handling duplicates."""
        if os.path.exists(target_path):
            return False, "File already exists in archive"

        try:
            shutil.move(file_path, target_path)
            return True, "Success"
        except Exception as e:
            return False, str(e)

    def _cleanup_empty_directories(self, root_dir, archive_dir):
        """Remove empty directories after archiving, excluding archive folder."""
        removed_count = 0
        abs_archive = os.path.abspath(archive_dir)
        abs_root = os.path.abspath(root_dir)

        for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
            if interrupt_current_processing():
                return removed_count

            abs_dirpath = os.path.abspath(dirpath)

            # Skip archive folder and root directory
            if abs_dirpath.startswith(abs_archive) or abs_dirpath == abs_root:
                continue

            try:
                if not os.listdir(dirpath):
                    os.rmdir(dirpath)
                    print(f"[Archive Node] Removed empty directory: {dirpath}")
                    removed_count += 1
            except FileNotFoundError:
                # Directory already removed
                pass
            except Exception as e:
                print(f"[Archive Node] Error removing directory {dirpath}: {e}")

        return removed_count

    def execute_archive(self, trigger, enabled=True, archive_folder_name="Archive",
                       skip_hidden_files=True, skip_extensions=".py,.js,.bat,.sh,.json,.yaml,.yml"):
        """Main execution method for the archive node."""
        print(f"\n[Archive Node] ========== ARCHIVE PROCESS STARTED ==========")
        print(f"[Archive Node] Enabled: {enabled}")
        print(f"[Archive Node] Archive Folder: {archive_folder_name}")

        if not enabled:
            status_msg = "Archiving is disabled."
            print(f"[Archive Node] {status_msg}")
            print(f"[Archive Node] ========== ARCHIVE PROCESS FINISHED ==========\n")
            return (status_msg,)

        # Setup directories
        current_output_dir = folder_paths.get_output_directory()
        self.archive_base_folder = os.path.join(current_output_dir, archive_folder_name)

        print(f"[Archive Node] Output directory: {current_output_dir}")
        print(f"[Archive Node] Archive location: {self.archive_base_folder}")

        if not self._ensure_directory_exists(self.archive_base_folder):
            status_msg = f"Error: Could not create archive folder: {self.archive_base_folder}"
            print(f"[Archive Node] {status_msg}")
            print(f"[Archive Node] ========== ARCHIVE PROCESS FINISHED ==========\n")
            return (status_msg,)

        # Parse skip extensions
        skip_ext_list = [ext.strip().lower() for ext in skip_extensions.split(',') if ext.strip()]
        print(f"[Archive Node] Skipping extensions: {skip_ext_list}")

        # Counters
        moved_count = 0
        skipped_count = 0
        error_count = 0

        # Process files
        print(f"[Archive Node] Scanning for files to archive...")

        for root, dirs, files in os.walk(current_output_dir, topdown=True):
            # Check for interruption
            if interrupt_current_processing():
                status_msg = "Archive process interrupted by user."
                print(f"[Archive Node] {status_msg}")
                print(f"[Archive Node] ========== ARCHIVE PROCESS FINISHED ==========\n")
                return (status_msg,)

            # Skip archive folder
            if os.path.abspath(root).startswith(os.path.abspath(self.archive_base_folder)):
                dirs[:] = []
                files[:] = []
                continue

            for file_name in files:
                # Check for interruption
                if interrupt_current_processing():
                    status_msg = "Archive process interrupted by user."
                    print(f"[Archive Node] {status_msg}")
                    print(f"[Archive Node] ========== ARCHIVE PROCESS FINISHED ==========\n")
                    return (status_msg,)

                file_path = os.path.join(root, file_name)

                # Skip files based on rules
                if self._should_skip_file(file_name, skip_hidden_files, skip_ext_list):
                    skipped_count += 1
                    continue

                # Get file date
                date_str = self._get_file_date_str(file_path)
                if not date_str:
                    skipped_count += 1
                    continue

                # Build target path
                relative_path = os.path.relpath(root, current_output_dir)

                if relative_path == ".":
                    target_folder = os.path.join(self.archive_base_folder, date_str)
                else:
                    target_folder = os.path.join(self.archive_base_folder, date_str, relative_path)

                # Ensure target directory exists
                if not self._ensure_directory_exists(target_folder):
                    print(f"[Archive Node] Failed to create target folder: {target_folder}")
                    error_count += 1
                    continue

                # Move file
                target_path = os.path.join(target_folder, file_name)
                success, message = self._move_file_to_archive(file_path, target_path)

                if success:
                    print(f"[Archive Node] Moved: {file_path} -> {target_path}")
                    moved_count += 1
                else:
                    if "already exists" in message:
                        skipped_count += 1
                    else:
                        print(f"[Archive Node] Error moving {file_path}: {message}")
                        error_count += 1

        print(f"[Archive Node] File archiving complete.")
        print(f"[Archive Node] Moved: {moved_count}, Skipped: {skipped_count}, Errors: {error_count}")

        # Cleanup empty directories
        print(f"[Archive Node] Cleaning up empty directories...")
        removed_dirs = self._cleanup_empty_directories(current_output_dir, self.archive_base_folder)
        print(f"[Archive Node] Removed {removed_dirs} empty directories.")

        # Final status
        status_msg = (
            f"Archive complete. Moved: {moved_count}, Skipped: {skipped_count}, "
            f"Errors: {error_count}, Empty dirs removed: {removed_dirs}. "
            f"Location: {self.archive_base_folder}"
        )

        print(f"[Archive Node] {status_msg}")
        print(f"[Archive Node] ========== ARCHIVE PROCESS FINISHED ==========\n")

        return (status_msg,)


# Node registration
NODE_CLASS_MAPPINGS = {
    "ArchiveOutputWorkflow": ArchiveOutputWorkflowNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArchiveOutputWorkflow": "Archive Output",
}
