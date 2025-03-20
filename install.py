import os
import sys
import subprocess

# Get the path to ComfyUI
comfyui_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

# Define the requirements file path
requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")

# Install dependencies
def install_requirements():
    """Installs dependencies from requirements.txt"""
    try:
        print("🔄 Installing dependencies from requirements.txt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], check=True)
        print("✅ Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to install dependencies: {e}")

install_requirements()
