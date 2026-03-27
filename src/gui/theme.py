"""
Theme Module - Dark mode theme with cobalt blue accents.
Professional styling inspired by Adobe-class editing tools.
"""


class DarkTheme:
    """Dark mode color scheme and stylesheet for the application."""

    # Color palette
    BG_PRIMARY = "#1a1a2e"
    BG_SECONDARY = "#16213e"
    BG_TERTIARY = "#0f3460"
    BG_SURFACE = "#1e1e3a"
    BG_INPUT = "#252547"

    ACCENT = "#2563eb"       # Cobalt blue
    ACCENT_HOVER = "#3b82f6"
    ACCENT_PRESSED = "#1d4ed8"

    TEXT_PRIMARY = "#e2e8f0"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_DISABLED = "#475569"

    BORDER = "#334155"
    BORDER_FOCUS = "#2563eb"

    SUCCESS = "#22c55e"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"

    REDACTION_OVERLAY = "#ef4444"
    REDACTION_CONFIRMED = "#000000"

    SCROLLBAR_BG = "#1e1e3a"
    SCROLLBAR_HANDLE = "#334155"

    @classmethod
    def get_stylesheet(cls) -> str:
        return f"""
        /* === Global === */
        QMainWindow, QDialog {{
            background-color: {cls.BG_PRIMARY};
            color: {cls.TEXT_PRIMARY};
            font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
            font-size: 13px;
        }}

        QWidget {{
            background-color: transparent;
            color: {cls.TEXT_PRIMARY};
        }}

        /* === Menu Bar === */
        QMenuBar {{
            background-color: {cls.BG_SECONDARY};
            color: {cls.TEXT_PRIMARY};
            border-bottom: 1px solid {cls.BORDER};
            padding: 2px;
        }}
        QMenuBar::item:selected {{
            background-color: {cls.ACCENT};
            border-radius: 4px;
        }}
        QMenu {{
            background-color: {cls.BG_SURFACE};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: 6px;
            padding: 4px;
        }}
        QMenu::item:selected {{
            background-color: {cls.ACCENT};
            border-radius: 4px;
        }}

        /* === Sidebar / Panels === */
        QFrame#sidebarFrame {{
            background-color: {cls.BG_SECONDARY};
            border-right: 1px solid {cls.BORDER};
            border-radius: 0px;
        }}
        QFrame#topBar {{
            background-color: {cls.BG_SECONDARY};
            border-bottom: 1px solid {cls.BORDER};
        }}

        /* === Labels === */
        QLabel {{
            color: {cls.TEXT_PRIMARY};
            background: transparent;
        }}
        QLabel#sectionTitle {{
            color: {cls.ACCENT_HOVER};
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        QLabel#statusLabel {{
            color: {cls.TEXT_SECONDARY};
            font-size: 12px;
        }}

        /* === Buttons === */
        QPushButton {{
            background-color: {cls.ACCENT};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 600;
            font-size: 13px;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: {cls.ACCENT_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {cls.ACCENT_PRESSED};
        }}
        QPushButton:disabled {{
            background-color: {cls.BG_TERTIARY};
            color: {cls.TEXT_DISABLED};
        }}
        QPushButton#secondaryButton {{
            background-color: {cls.BG_INPUT};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
        }}
        QPushButton#secondaryButton:hover {{
            background-color: {cls.BG_TERTIARY};
            border-color: {cls.ACCENT};
        }}
        QPushButton#dangerButton {{
            background-color: {cls.ERROR};
        }}
        QPushButton#dangerButton:hover {{
            background-color: #dc2626;
        }}

        /* === Checkboxes === */
        QCheckBox {{
            color: {cls.TEXT_PRIMARY};
            spacing: 8px;
            font-size: 13px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {cls.BORDER};
            border-radius: 4px;
            background-color: {cls.BG_INPUT};
        }}
        QCheckBox::indicator:checked {{
            background-color: {cls.ACCENT};
            border-color: {cls.ACCENT};
        }}
        QCheckBox::indicator:hover {{
            border-color: {cls.ACCENT_HOVER};
        }}

        /* === Progress Bar === */
        QProgressBar {{
            background-color: {cls.BG_INPUT};
            border: 1px solid {cls.BORDER};
            border-radius: 6px;
            text-align: center;
            color: {cls.TEXT_PRIMARY};
            font-size: 11px;
            min-height: 20px;
        }}
        QProgressBar::chunk {{
            background-color: {cls.ACCENT};
            border-radius: 5px;
        }}

        /* === Scroll Bars === */
        QScrollBar:vertical {{
            background: {cls.SCROLLBAR_BG};
            width: 10px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical {{
            background: {cls.SCROLLBAR_HANDLE};
            min-height: 30px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {cls.ACCENT};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background: {cls.SCROLLBAR_BG};
            height: 10px;
            border-radius: 5px;
        }}
        QScrollBar::handle:horizontal {{
            background: {cls.SCROLLBAR_HANDLE};
            min-width: 30px;
            border-radius: 5px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {cls.ACCENT};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        /* === Combo Box === */
        QComboBox {{
            background-color: {cls.BG_INPUT};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: 6px;
            padding: 6px 12px;
            min-height: 20px;
        }}
        QComboBox:hover {{
            border-color: {cls.ACCENT};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {cls.BG_SURFACE};
            color: {cls.TEXT_PRIMARY};
            selection-background-color: {cls.ACCENT};
            border: 1px solid {cls.BORDER};
        }}

        /* === Splitter === */
        QSplitter::handle {{
            background-color: {cls.BORDER};
        }}
        QSplitter::handle:horizontal {{
            width: 2px;
        }}

        /* === Tab Widget === */
        QTabWidget::pane {{
            border: 1px solid {cls.BORDER};
            border-radius: 6px;
            background-color: {cls.BG_SURFACE};
        }}
        QTabBar::tab {{
            background-color: {cls.BG_INPUT};
            color: {cls.TEXT_SECONDARY};
            padding: 8px 16px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background-color: {cls.ACCENT};
            color: white;
        }}

        /* === ToolTip === */
        QToolTip {{
            background-color: {cls.BG_SURFACE};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: 4px;
            padding: 4px 8px;
        }}

        /* === GroupBox === */
        QGroupBox {{
            border: 1px solid {cls.BORDER};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 16px;
            font-weight: 600;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: {cls.ACCENT_HOVER};
        }}
        """
