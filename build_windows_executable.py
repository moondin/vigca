"""
Build script for creating a standalone Windows executable for ViGCA.

This script uses PyInstaller to package the ViGCA application into a 
standalone .exe file with all dependencies included.
"""
import os
import subprocess
import shutil
import sys

# Configuration
APP_NAME = "ViGCA"
APP_VERSION = "0.1.0"
MAIN_SCRIPT = "run_vigca.py"
ICON_FILE = "resources/vigca_icon.ico"
OUTPUT_DIR = "dist"

def ensure_dependencies():
    """Install required dependencies for building."""
    print("Ensuring build dependencies are installed...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def create_resources():
    """Create necessary resource files."""
    print("Creating resource directory...")
    os.makedirs("resources", exist_ok=True)
    
    # If icon doesn't exist, we could generate one or use a placeholder
    if not os.path.exists(ICON_FILE):
        print(f"Note: Icon file {ICON_FILE} not found. Using default icon.")

def build_executable():
    """Build the executable using PyInstaller."""
    print(f"Building {APP_NAME} v{APP_VERSION} executable...")
    
    # Basic PyInstaller command
    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--onefile",  # Create a single .exe file
        "--windowed",  # Don't show console window
        "--clean",  # Clean PyInstaller cache
        "--add-data", "resources;resources",  # Include resources directory
    ]
    
    # Add icon if available
    if os.path.exists(ICON_FILE):
        cmd.extend(["--icon", ICON_FILE])
    
    # Add main script
    cmd.append(MAIN_SCRIPT)
    
    # Run PyInstaller
    subprocess.check_call(cmd)
    
    print(f"Executable built successfully: {OUTPUT_DIR}/{APP_NAME}.exe")

def cleanup():
    """Clean up temporary build files."""
    print("Cleaning up build files...")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists(f"{APP_NAME}.spec"):
        os.remove(f"{APP_NAME}.spec")

def create_installer():
    """Create an installer using NSIS (optional)."""
    # This would require NSIS to be installed, so we'll skip implementation for now
    print("Note: NSIS installer creation not implemented in this script.")
    print("To create an installer, consider using NSIS manually with the generated executable.")

def main():
    """Main build process."""
    try:
        ensure_dependencies()
        create_resources()
        build_executable()
        cleanup()
        print("Build completed successfully!")
        print(f"Executable is available at: {os.path.abspath(f'{OUTPUT_DIR}/{APP_NAME}.exe')}")
    except Exception as e:
        print(f"Error during build process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()