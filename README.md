# ViGCA: Vision-Guided Cursor Automation

![ViGCA Logo](https://your-logo-url-here.png)

ViGCA is an AI-powered application that watches your screen, learns visual targets, and automatically moves your mouse cursor to those targets when they appear. It's perfect for automating repetitive tasks, creating assistive technology solutions, or building custom UI testing tools.

## Features

- **Screen Monitoring**: Continuously monitors your screen for visual targets
- **Target Learning**: Easily create and manage visual targets by selecting regions on your screen
- **Smart Detection**: Uses computer vision algorithms to accurately identify targets even with slight variations
- **Automated Cursor Control**: Precisely moves the cursor to detected targets
- **Configuration Options**: Customize detection methods, confidence thresholds, cursor movement style, and more
- **Modern Windows UI**: Clean, modern interface optimized for Windows 11
- **Programmable API**: Use the core functionality in your own Python scripts

## Demo

[View Demo Video](https://your-demo-video-url-here.mp4)

## Windows Installation

### Easy Installation (Recommended)

1. **Download** the latest release from [GitHub Releases](https://github.com/your-username/vigca/releases)
2. **Run** the `ViGCA_Setup.exe` installer
3. **Launch** ViGCA from the desktop shortcut or Start Menu

### Advanced Installation (From Source)

For Windows developers or advanced users who want to install from source:

1. **Clone** the repository:
   ```bash
   git clone https://github.com/your-username/vigca.git
   cd vigca
   ```

2. **Run** the Windows installer script:
   ```bash
   python windows_install.py
   ```

This will:
- Install all dependencies
- Create desktop and Start Menu shortcuts
- Register the application
- Offer to launch the application when done

### Requirements

- Windows 10/11 (64-bit)
- Python 3.8 or higher

For detailed installation instructions for all platforms, see [INSTALL.md](INSTALL.md).

## Quick Start

### Windows Application

Simply double-click the ViGCA desktop shortcut or find it in your Start Menu.

Alternatively, run it directly:
```bash
python run_vigca_windows.py
```

### Programmatic Usage

```python
from vigca.screen_capture import ScreenCapture
from vigca.feature_extraction import FeatureExtractor
from vigca.target_manager import TargetManager
from vigca.cursor_control import CursorController

# Initialize components
screen_capture = ScreenCapture()
feature_extractor = FeatureExtractor()
target_manager = TargetManager()
cursor_controller = CursorController()

# Capture screen
frame = screen_capture.capture()

# Find targets in the captured frame
for target_id, target in target_manager.get_all_targets().items():
    matches = feature_extractor.find_matches(target.features, frame)
    for match in matches:
        # Move cursor to the matched target
        cursor_controller.move_to_target(match)
        break
```

See the [examples](examples/) directory for more detailed usage examples.

## User Guide

### Training Targets

1. Launch the application
2. Click "Start Training"
3. Select a region on the screen that you want to detect
4. Give the target a name
5. Repeat for additional targets
6. Toggle which targets should be active

### Running Detection

1. Enable the targets you want to detect
2. Click "Start Detection"
3. The cursor will automatically move to detected targets

### Configuration

- **Screen Capture**: Adjust the capture rate, set a region of interest
- **Detection**: Choose the method, adjust confidence threshold
- **Cursor Control**: Set movement speed, toggle smooth movement

## How It Works

ViGCA combines several technologies:

1. **Screen Capture**: Continuously grabs screenshots at a configurable rate
2. **Feature Extraction**: Applies computer vision algorithms to identify unique visual patterns
3. **Pattern Matching**: Compares stored targets against the current screen content
4. **Cursor Control**: Uses PyAutoGUI to precisely control the mouse cursor

## Use Cases

- **Automation**: Click buttons or interact with UI elements based on their appearance
- **Gaming**: Create visual macros that respond to in-game events
- **Accessibility**: Build assistive technology that helps users with limited mobility
- **Testing**: Develop UI testing tools that can verify visual elements

## Creating a Standalone Executable

You can create a standalone executable that doesn't require Python:

```bash
python build_windows_executable.py
```

This will create `dist/ViGCA.exe` - a single file that can be distributed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenCV for computer vision capabilities
- PyAutoGUI for cursor control
- MSS for fast screen capture
- CustomTkinter for the modern UI elements
- All our contributors and users!