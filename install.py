import os
import sys
import subprocess

def install_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        try:
            print("🔧 Installing requirements...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install requirements: {e}")

install_requirements()
