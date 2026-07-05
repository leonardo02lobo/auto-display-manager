"""
Main entry point for Auto Display Manager
"""

import sys
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from gui.main_window import MainWindow


def main():
    """Main application entry point"""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Auto Display Manager")
    app.setOrganizationName("Auto Display Manager")
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Handle SIGINT for clean exit
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
