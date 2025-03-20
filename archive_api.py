import os
import shutil
from datetime import datetime
from flask import request, jsonify
import folder_paths

# Define the archive function
def archive_files():
    """Moves files to archive/YYYY-MM-DD/, preserving subdirectories."""
    output_folder = folder_paths.get_output_directory()
    archive_folder = os.path.join(output_folder, "archive")

    def ensure_directory_exists(path):
        """Ensures the given directory exists."""
        if not os.path.exists(path):
            os.makedirs(path)

    def get_creation_date(file_path):
        """Returns the creation date of a file in YYYY-MM-DD format."""
        try:
            creation_time = os.path.getctime(file_path)
            return datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d")
        except Exception:
            return None

    ensure_directory_exists(archive_folder)

    for root, _, files in os.walk(output_folder):
        if "archive" in root:
            continue  # Skip the archive folder itself

        for file in files:
            file_path = os.path.join(root, file)

            # Skip script files
            if file.lower().endswith((".py", ".bat")) or file.startswith("."):
                continue

            # Get the creation date
            creation_date = get_creation_date(file_path)
            if not creation_date:
                continue

            # Compute the relative path
            relative_path = os.path.relpath(root, output_folder)
            archive_path = os.path.join(archive_folder, creation_date, relative_path)

            # Ensure the archive directory exists
            ensure_directory_exists(archive_path)

            # Move the file
            new_file_path = os.path.join(archive_path, file)
            try:
                shutil.move(file_path, new_file_path)
            except Exception as e:
                return f"Error moving {file_path}: {e}"

    return "Archiving complete! Check the output/archive/ folder."

# Register API endpoint for ComfyUI
def register_api(app):
    @app.route("/archive-output", methods=["POST"])
    def api_archive_output():
        response = archive_files()
        return jsonify({"message": response})
