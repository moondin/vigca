"""
Windows Installation Script for ViGCA

This script simplifies the installation process for Windows users.
"""
import os
import sys
import subprocess
import ctypes
import winreg
import tempfile
import time
import shutil
from pathlib import Path

# Configuration
APP_NAME = "ViGCA"
APP_VERSION = "0.1.0"
GITHUB_URL = "https://github.com/your-username/vigca"  # Update this with your GitHub repo
DESKTOP_SHORTCUT = True
START_MENU_SHORTCUT = True
RESOURCE_DIR = "resources"

def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def print_header():
    """Print the installation header."""
    print("\n" + "=" * 60)
    print(f"{APP_NAME} v{APP_VERSION} - Windows Installation")
    print("=" * 60 + "\n")

def check_python_version():
    """Check if the Python version is compatible."""
    print("Checking Python version...")
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 8):
        print(f"Error: Python 3.8 or higher is required (found {major}.{minor}).")
        return False
    print(f"Found Python {major}.{minor} ✓")
    return True

def create_directories():
    """Create necessary directories."""
    print("Creating application directories...")
    
    # Create resources directory
    os.makedirs(RESOURCE_DIR, exist_ok=True)
    print(f"Created {RESOURCE_DIR} directory ✓")
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    print("Created logs directory ✓")
    
    return True

def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    try:
        # Install dependencies from requirements file
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements-windows.txt"
        ])
        print("Dependencies installed successfully ✓")
        return True
    except subprocess.CalledProcessError:
        print("Error: Failed to install dependencies.")
        return False

def register_app():
    """Register the application in Windows registry."""
    try:
        # Get the current script directory
        app_path = os.path.abspath(sys.executable)
        script_path = os.path.abspath("run_vigca_windows.py")
        
        # Create registry key for the application
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\{APP_NAME}") as key:
            winreg.SetValueEx(key, "Version", 0, winreg.REG_SZ, APP_VERSION)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, os.path.dirname(script_path))
            winreg.SetValueEx(key, "PythonPath", 0, winreg.REG_SZ, app_path)
        
        print("Application registered in Windows registry ✓")
        return True
    except Exception as e:
        print(f"Warning: Unable to register application in registry: {e}")
        return True  # Continue anyway

def create_shortcuts():
    """Create desktop and Start Menu shortcuts."""
    try:
        # Get paths
        script_path = os.path.abspath("run_vigca_windows.py")
        python_path = sys.executable
        
        # Create desktop shortcut
        if DESKTOP_SHORTCUT:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop_path, f"{APP_NAME}.lnk")
            
            # Create shortcut using PowerShell
            ps_command = f'''
            $WshShell = New-Object -comObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
            $Shortcut.TargetPath = "{python_path}"
            $Shortcut.Arguments = "{script_path}"
            $Shortcut.WorkingDirectory = "{os.path.dirname(script_path)}"
            $Shortcut.Description = "{APP_NAME} - Vision-Guided Cursor Automation"
            $Shortcut.IconLocation = "{os.path.abspath(os.path.join(RESOURCE_DIR, 'vigca_icon.ico'))}"
            $Shortcut.Save()
            '''
            
            # Execute PowerShell command
            with tempfile.NamedTemporaryFile(suffix='.ps1', delete=False) as temp:
                temp.write(ps_command.encode('utf-8'))
                temp_path = temp.name
            
            subprocess.call(['powershell', '-ExecutionPolicy', 'Bypass', '-File', temp_path])
            os.unlink(temp_path)
            
            print("Desktop shortcut created ✓")
        
        # Create Start Menu shortcut
        if START_MENU_SHORTCUT:
            start_menu_path = os.path.join(
                os.environ.get('APPDATA', ''),
                "Microsoft\\Windows\\Start Menu\\Programs"
            )
            app_folder = os.path.join(start_menu_path, APP_NAME)
            os.makedirs(app_folder, exist_ok=True)
            
            shortcut_path = os.path.join(app_folder, f"{APP_NAME}.lnk")
            
            # Create shortcut using PowerShell
            ps_command = f'''
            $WshShell = New-Object -comObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
            $Shortcut.TargetPath = "{python_path}"
            $Shortcut.Arguments = "{script_path}"
            $Shortcut.WorkingDirectory = "{os.path.dirname(script_path)}"
            $Shortcut.Description = "{APP_NAME} - Vision-Guided Cursor Automation"
            $Shortcut.IconLocation = "{os.path.abspath(os.path.join(RESOURCE_DIR, 'vigca_icon.ico'))}"
            $Shortcut.Save()
            '''
            
            # Execute PowerShell command
            with tempfile.NamedTemporaryFile(suffix='.ps1', delete=False) as temp:
                temp.write(ps_command.encode('utf-8'))
                temp_path = temp.name
            
            subprocess.call(['powershell', '-ExecutionPolicy', 'Bypass', '-File', temp_path])
            os.unlink(temp_path)
            
            print("Start Menu shortcut created ✓")
        
        return True
    except Exception as e:
        print(f"Warning: Unable to create shortcuts: {e}")
        return True  # Continue anyway

def install_app():
    """Install the application in development mode."""
    print("Installing application...")
    try:
        # Install the package in development mode
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-e", "."
        ])
        print("Application installed successfully ✓")
        return True
    except subprocess.CalledProcessError:
        print("Error: Failed to install application.")
        return False

def get_icon():
    """Create or download an icon for the application."""
    icon_path = os.path.join(RESOURCE_DIR, "vigca_icon.ico")
    
    # Check if icon already exists
    if os.path.exists(icon_path):
        print("Icon file already exists ✓")
        return True
    
    # Generate a simple icon
    try:
        print("Generating application icon...")
        
        # Simple method to generate a very basic icon
        # In a real application, you would want to use a proper icon file
        # Here we're just creating a placeholder for demonstration purposes
        
        # Try to import PIL
        try:
            from PIL import Image, ImageDraw
            
            # Create a simple colored square icon
            img = Image.new('RGBA', (256, 256), color=(0, 120, 212, 255))
            draw = ImageDraw.Draw(img)
            
            # Draw a simple shape to represent the application
            draw.ellipse((50, 50, 206, 206), fill=(255, 255, 255, 255))
            draw.rectangle((90, 90, 166, 166), fill=(0, 120, 212, 255))
            
            # Save as ICO
            img.save(icon_path, format="ICO")
            
            print("Icon generated successfully ✓")
            return True
        except ImportError:
            print("Warning: Unable to generate icon (PIL not available).")
            # Create an empty file as placeholder
            with open(icon_path, 'wb') as f:
                f.write(b'')
            return True
    except Exception as e:
        print(f"Warning: Unable to generate icon: {e}")
        return True  # Continue anyway

def main():
    """Main installation process."""
    print_header()
    
    # Check if running as admin (for registry changes)
    if not is_admin() and os.name == 'nt':
        print("Note: Running without administrator privileges.")
        print("Some features (like registry entries) might not be available.")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Get/create icon
    if not get_icon():
        print("Warning: Failed to get application icon.")
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Install the application
    if not install_app():
        sys.exit(1)
    
    # Register app in Windows registry
    if os.name == 'nt':
        register_app()
    
    # Create shortcuts
    if os.name == 'nt':
        create_shortcuts()
    
    # Installation completed
    print("\n" + "=" * 60)
    print(f"{APP_NAME} v{APP_VERSION} installation completed successfully!")
    print("=" * 60 + "\n")
    
    # Ask to launch the application
    launch = input("Do you want to launch the application now? (y/n): ").strip().lower()
    if launch == 'y':
        print(f"Launching {APP_NAME}...")
        subprocess.Popen([sys.executable, "run_vigca_windows.py"])
    else:
        print(f"You can launch {APP_NAME} later by running 'run_vigca_windows.py'")
        print("or by using the desktop/Start Menu shortcuts.")
    
    print("\nThank you for installing ViGCA!")
    time.sleep(2)

if __name__ == "__main__":
    main()