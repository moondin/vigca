# Installation Instructions for ViGCA

## Windows Installation (Recommended)

ViGCA offers a streamlined installation experience for Windows 10/11 users with both a standalone installer and an easy installation script.

### Option 1: Standalone Installer (Easiest)

1. **Download** the latest installer from [GitHub Releases](https://github.com/your-username/vigca/releases)
2. **Run** `ViGCA_Setup.exe` and follow the installation wizard
3. **Launch** ViGCA from the desktop shortcut or Start Menu

### Option 2: Installation Script (For Developers)

If you've cloned the repository or downloaded the source code:

1. Ensure Python 3.8 or higher is installed on your system
2. Open Command Prompt or PowerShell
3. Navigate to the ViGCA directory
4. Run the Windows installer script:

```powershell
python windows_install.py
```

This script will:
- Install all required dependencies
- Create desktop and Start Menu shortcuts
- Register the application in Windows
- Offer to launch the application immediately

### Option 3: Manual Installation (Advanced)

For complete control over the installation process:

1. Clone the repository and navigate to the directory:
   ```powershell
   git clone https://github.com/your-username/vigca.git
   cd vigca
   ```

2. Create and activate a virtual environment (recommended):
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```powershell
   pip install -r requirements-windows.txt
   ```

4. Install the package in development mode:
   ```powershell
   pip install -e .
   ```

5. Run the Windows version of the application:
   ```powershell
   python run_vigca_windows.py
   ```

### Creating a Standalone Executable

To create a portable executable that doesn't require Python:

```powershell
python build_windows_executable.py
```

This creates `dist/ViGCA.exe` - a single file that can be distributed and run on any Windows 10/11 system without Python installed.

## Cross-Platform Installation

ViGCA works across multiple platforms, but requires different setup steps for each operating system.

### Prerequisites

Before installing ViGCA, ensure you have:

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment tool (recommended)

### Operating System Specific Requirements

#### macOS

- XQuartz (for X11 support): `brew install --cask xquartz`

#### Linux

- X11 development libraries: 
  - Debian/Ubuntu: `sudo apt-get install python3-dev python3-tk python3-pip libx11-dev`
  - Fedora: `sudo dnf install python3-devel python3-tkinter python3-pip libX11-devel`
  - Arch: `sudo pacman -S python python-pip tk libx11`

### Cross-Platform Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/vigca.git
   cd vigca
   ```

2. Create and activate a virtual environment:
   ```bash
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Install the application:
   ```bash
   pip install -e .
   ```

## Running ViGCA

### On Windows

```powershell
# Using the Windows-optimized UI
python run_vigca_windows.py

# Or using the classic UI
python run_vigca.py
```

### On macOS/Linux

```bash
# Using the launcher script
python run_vigca.py

# Or directly invoke the package
python -m vigca.main
```

## Troubleshooting

### Windows Issues

- **Missing modules**: Make sure you've installed all dependencies with `pip install -r requirements-windows.txt`
- **Permission errors**: Try running the commands with administrator privileges
- **DLL errors**: Ensure you have the latest Visual C++ Redistributable installed

### X11 Errors (macOS/Linux)

- **macOS**: Verify XQuartz is installed and running
- **Linux**: Install the appropriate X11 development packages for your distribution

### PyAutoGUI Fails to Import

This is usually caused by missing dependencies:

- **Windows**: Ensure you have Microsoft Visual C++ Build Tools installed
- **macOS**: You may need to install additional libraries via brew
- **Linux**: Install the required development packages (see OS-specific requirements)

## Uninstallation

### Windows

1. Use the Windows Control Panel "Add or Remove Programs" feature
2. Or run the uninstaller from the installation directory

### Manual Uninstallation (All platforms)

1. If installed in development mode:
   ```bash
   pip uninstall vigca
   ```

2. Remove any configuration files (optional):
   ```bash
   # Windows
   del %USERPROFILE%\vigca_config.json
   del %USERPROFILE%\targets.pkl
   
   # macOS/Linux
   rm ~/.vigca_config.json
   rm ~/.vigca_targets.pkl
   ```