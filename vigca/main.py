"""
Vision-Guided Cursor Automation (ViGCA)

Main entry point for the application that integrates all modules and 
launches the user interface.
"""
import os
import sys
import logging
import tkinter as tk
from vigca.gui import VigcaGUI

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

def main():
    """Main entry point for the ViGCA application."""
    # Setup logging
    logger = setup_logging()
    
    try:
        # Initialize the root window
        root = tk.Tk()
        root.title("Vision-Guided Cursor Automation (ViGCA)")
        
        # Set minimum size for the window
        root.minsize(1000, 700)
        
        # Create and pack the main application UI
        app = VigcaGUI(root)
        app.pack(fill=tk.BOTH, expand=True)
        
        # Start the main event loop
        root.mainloop()
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()