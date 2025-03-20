import os
import shutil

# Define paths
comfyui_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))  # Get ComfyUI root
ui_folder = os.path.join(comfyui_base, "web", "extensions", "ui")
source_js = os.path.join(os.path.dirname(__file__), "web", "extensions", "ui", "custom_ui.js")
destination_js = os.path.join(ui_folder, "custom_ui.js")

# Ensure UI extensions folder exists
if not os.path.exists(ui_folder):
    os.makedirs(ui_folder)

# Copy custom_ui.js to the correct location
try:
    shutil.copy2(source_js, destination_js)
    print(f"✅ Installed custom UI file: {destination_js}")
except Exception as e:
    print(f"❌ ERROR: Failed to install custom UI file: {e}")
