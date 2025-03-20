import os
import sys
import subprocess
import shutil

# Get ComfyUI base directory
comfyui_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

# Get paths
ui_folder = os.path.join(comfyui_base, "web", "extensions", "ui")
source_js = os.path.join(os.path.dirname(__file__), "web", "extensions", "ui", "custom_ui.js")
destination_js = os.path.join(ui_folder, "custom_ui.js")
requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")

# Ensure Python is available
def install_requirements():
    """Installs dependencies from requirements.txt"""
    try:
        print("🔄 Installing dependencies from requirements.txt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], check=True)
        print("✅ Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to install dependencies: {e}")

# Ensure UI extensions folder exists
if not os.path.exists(ui_folder):
    os.makedirs(ui_folder)

# Copy custom_ui.js to the correct location
try:
    shutil.copy2(source_js, destination_js)
    print(f"✅ Installed custom UI file: {destination_js}")
except Exception as e:
    print(f"❌ ERROR: Failed to install custom UI file: {e}")

# Install dependencies
install_requirements()
