import os
import shutil
from datetime import datetime
import folder_paths

def archive_files():
    """Moves files from the output directory into an archive folder structured by date, and removes empty folders."""
    output_folder = folder_paths.get_output_directory()
    archive_folder = os.path.join(output_folder, "archive")

    def ensure_directory_exists(path):
        if not os.path.exists(path):
            os.makedirs(path)

    def get_creation_date(file_path):
        try:
            creation_time = os.path.getctime(file_path)
            return datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d")
        except Exception:
            return None

    ensure_directory_exists(archive_folder)

    moved_files = 0
    skipped_files = 0
    for root, _, files in os.walk(output_folder):
        if "archive" in root:
            continue  # Skip archive

        for file in files:
            file_path = os.path.join(root, file)

            if file.lower().endswith((".py", ".bat")) or file.startswith("."):
                skipped_files += 1
                continue

            creation_date = get_creation_date(file_path)
            if not creation_date:
                skipped_files += 1
                continue

            relative_path = os.path.relpath(root, output_folder)
            archive_path = os.path.join(archive_folder, creation_date, relative_path)
            ensure_directory_exists(archive_path)

            new_file_path = os.path.join(archive_path, file)
            try:
                shutil.move(file_path, new_file_path)
                moved_files += 1
            except Exception:
                skipped_files += 1

    # Clean up empty folders
    removed_dirs = 0
    for root, dirs, _ in os.walk(output_folder, topdown=False):
        if "archive" in root:
            continue
        for d in dirs:
            dir_path = os.path.join(root, d)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    removed_dirs += 1
            except Exception:
                continue

    return (
        f"✅ Archive complete!\n"
        f"- Moved files: {moved_files}\n"
        f"- Skipped files: {skipped_files}\n"
        f"- Removed empty folders: {removed_dirs}\n"
        f"- Output: output/archive/YYYY-MM-DD/"
    )
