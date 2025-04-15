"""
Windows Main Module for ViGCA

Entry point for the Windows application with modern UI.
"""
import os
import sys
import logging
import ctypes
import customtkinter as ctk
from vigca.windows_gui import WindowsVigcaGUI

def setup_logging():
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure logging to file and console
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join("logs", "vigca.log")),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def set_dpi_awareness():
    """Enable DPI awareness for better rendering on high-DPI displays."""
    try:
        # Windows 8.1 and later
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except AttributeError:
        try:
            # Earlier Windows versions
            ctypes.windll.user32.SetProcessDPIAware()
        except AttributeError:
            pass

def main():
    """Main entry point for the Windows ViGCA application."""
    # Setup logging
    logger = setup_logging()
    
    try:
        # Set DPI awareness
        set_dpi_awareness()
        
        # Configure CustomTkinter appearance
        ctk.set_appearance_mode("System")  # "System", "Dark", "Light"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
        
        # Create the main window
        app = ctk.CTk()
        app.title("ViGCA - Vision-Guided Cursor Automation")
        app.geometry("1200x800")
        app.minsize(900, 600)
        
        # Set app icon
        if os.path.exists("resources/vigca_icon.ico"):
            app.iconbitmap("resources/vigca_icon.ico")
        
        # Create and pack the main application UI
        gui = WindowsVigcaGUI(app)
        gui.pack(fill="both", expand=True)
        
        # Start the main event loop
        app.mainloop()
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()