"""
AI Document Redactor Pro - Main Entry Point
100% Offline Document Redaction Tool
"""

import logging
import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from gui.main_window import MainWindow
from gui.theme import DarkTheme
from utils.config import AppConfig


def setup_logging():
    """Configure application logging."""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting AI Document Redactor Pro")

    config = AppConfig.load()

    app = QApplication(sys.argv)
    app.setApplicationName("AI Document Redactor Pro")
    app.setOrganizationName("RedactorPro")
    app.setApplicationVersion("1.0.0")

    # Apply dark theme
    app.setStyleSheet(DarkTheme.get_stylesheet())

    window = MainWindow()
    window.resize(config.window_width, config.window_height)
    window.show()

    logger.info("Application ready")
    exit_code = app.exec()

    config.save()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
