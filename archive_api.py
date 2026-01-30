"""
ComfyUI Archive Output API
Server-side API endpoints for the archive output functionality.
"""

import os
import shutil
from datetime import datetime
import folder_paths
from aiohttp import web


class ArchiveService:
    """Service class for archiving ComfyUI output files."""

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    def _ensure_directory_exists(self, path):
        """Create directory if it doesn't exist."""
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
                return True
            except Exception as e:
                print(f"[Archive API] Error creating directory {path}: {e}")
                return False
        return True

    def _get_file_date_str(self, file_path):
        """Get file modification date as YYYY-MM-DD string."""
        try:
            stat_time = os.path.getmtime(file_path)
            return datetime.fromtimestamp(stat_time).strftime("%Y-%m-%d")
        except Exception as e:
            print(f"[Archive API] Error getting date for {file_path}: {e}")
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
            abs_dirpath = os.path.abspath(dirpath)

            # Skip archive folder and root directory
            if abs_dirpath.startswith(abs_archive) or abs_dirpath == abs_root:
                continue

            try:
                if not os.listdir(dirpath):
                    os.rmdir(dirpath)
                    print(f"[Archive API] Removed empty directory: {dirpath}")
                    removed_count += 1
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"[Archive API] Error removing directory {dirpath}: {e}")

        return removed_count

    def execute_archive(self, config):
        """
        Execute the archive operation with the provided configuration.

        Args:
            config (dict): Configuration with keys:
                - archive_folder_name (str): Name of the archive folder
                - skip_hidden_files (bool): Whether to skip hidden files
                - skip_extensions (str): Comma-separated list of extensions to skip

        Returns:
            dict: Result with success status and statistics
        """
        print(f"\n[Archive API] ========== ARCHIVE PROCESS STARTED ==========")

        # Extract configuration
        archive_folder_name = config.get("archive_folder_name", "Archive")
        skip_hidden_files = config.get("skip_hidden_files", True)
        skip_extensions = config.get("skip_extensions", ".py,.js,.bat,.sh,.json,.yaml,.yml")

        print(f"[Archive API] Archive Folder: {archive_folder_name}")
        print(f"[Archive API] Skip Hidden Files: {skip_hidden_files}")
        print(f"[Archive API] Skip Extensions: {skip_extensions}")

        # Setup directories
        current_output_dir = folder_paths.get_output_directory()
        archive_base_folder = os.path.join(current_output_dir, archive_folder_name)

        print(f"[Archive API] Output directory: {current_output_dir}")
        print(f"[Archive API] Archive location: {archive_base_folder}")

        if not self._ensure_directory_exists(archive_base_folder):
            return {
                "success": False,
                "error": f"Could not create archive folder: {archive_base_folder}",
                "moved": 0,
                "skipped": 0,
                "errors": 0,
                "removed_dirs": 0
            }

        # Parse skip extensions
        skip_ext_list = [ext.strip().lower() for ext in skip_extensions.split(',') if ext.strip()]
        print(f"[Archive API] Skipping extensions: {skip_ext_list}")

        # Counters
        moved_count = 0
        skipped_count = 0
        error_count = 0

        # Process files
        print(f"[Archive API] Scanning for files to archive...")

        for root, dirs, files in os.walk(current_output_dir, topdown=True):
            # Skip archive folder
            if os.path.abspath(root).startswith(os.path.abspath(archive_base_folder)):
                dirs[:] = []
                files[:] = []
                continue

            # Modify dirs in-place to skip specific folders and those starting with _
            # This prevents os.walk from entering these directories
            dirs[:] = [d for d in dirs if d not in ["database"] and not d.startswith("_")]

            for file_name in files:
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
                    target_folder = os.path.join(archive_base_folder, date_str)
                else:
                    target_folder = os.path.join(archive_base_folder, date_str, relative_path)

                # Ensure target directory exists
                if not self._ensure_directory_exists(target_folder):
                    print(f"[Archive API] Failed to create target folder: {target_folder}")
                    error_count += 1
                    continue

                # Move file
                target_path = os.path.join(target_folder, file_name)
                success, message = self._move_file_to_archive(file_path, target_path)

                if success:
                    print(f"[Archive API] Moved: {file_path} -> {target_path}")
                    moved_count += 1
                else:
                    if "already exists" in message:
                        skipped_count += 1
                    else:
                        print(f"[Archive API] Error moving {file_path}: {message}")
                        error_count += 1

        print(f"[Archive API] File archiving complete.")
        print(f"[Archive API] Moved: {moved_count}, Skipped: {skipped_count}, Errors: {error_count}")

        # Cleanup empty directories
        print(f"[Archive API] Cleaning up empty directories...")
        removed_dirs = self._cleanup_empty_directories(current_output_dir, archive_base_folder)
        print(f"[Archive API] Removed {removed_dirs} empty directories.")

        print(f"[Archive API] ========== ARCHIVE PROCESS FINISHED ==========\n")

        return {
            "success": True,
            "moved": moved_count,
            "skipped": skipped_count,
            "errors": error_count,
            "removed_dirs": removed_dirs,
            "archive_location": archive_base_folder
        }


# Global service instance
archive_service = ArchiveService()


def setup_routes(routes):
    """
    Setup API routes for archive functionality.

    Args:
        routes: The PromptServer routes object
    """

    @routes.post("/archive/execute")
    async def execute_archive_endpoint(request):
        """Execute the archive operation."""
        try:
            json_data = await request.json()
            result = archive_service.execute_archive(json_data)
            return web.json_response(result)
        except Exception as e:
            print(f"[Archive API] Error in execute endpoint: {e}")
            return web.json_response({
                "success": False,
                "error": str(e),
                "moved": 0,
                "skipped": 0,
                "errors": 0,
                "removed_dirs": 0
            }, status=500)

    @routes.get("/archive/status")
    async def get_archive_status(request):
        """Get current archive directory status."""
        try:
            output_dir = folder_paths.get_output_directory()

            # Count files in output directory (excluding archive folders)
            file_count = 0
            for root, dirs, files in os.walk(output_dir):
                # Skip if in any Archive folder
                if "Archive" in root or "archive" in root:
                    continue
                file_count += len([f for f in files if not f.startswith(".")])

            return web.json_response({
                "success": True,
                "output_directory": output_dir,
                "file_count": file_count
            })
        except Exception as e:
            print(f"[Archive API] Error in status endpoint: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    print("[Archive API] Routes registered successfully")
