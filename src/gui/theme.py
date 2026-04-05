"""
Premium Dark Theme - Modern, professional styling for Document Redactor Pro.
Cobalt blue accents on deep dark backgrounds.
"""

from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication


# ── Color Palette ──────────────────────────────────────────────
class Colors:
    # Backgrounds
    BG_DARKEST = "#0f1117"      # Main window background
    BG_DARK = "#161822"         # Panels, sidebar
    BG_MEDIUM = "#1e2030"       # Cards, input fields
    BG_LIGHT = "#262940"        # Hover states
    BG_LIGHTER = "#2e3150"      # Active/selected states

    # Accent - Cobalt Blue
    ACCENT = "#2563eb"
    ACCENT_HOVER = "#3b82f6"
    ACCENT_PRESSED = "#1d4ed8"
    ACCENT_SOFT = "#1e3a5f"     # Subtle accent backgrounds

    # Text
    TEXT_PRIMARY = "#e8eaf0"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"
    TEXT_ON_ACCENT = "#ffffff"

    # Borders
    BORDER = "#2a2d42"
    BORDER_LIGHT = "#363a54"
    BORDER_FOCUS = "#2563eb"

    # Status
    SUCCESS = "#22c55e"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"

    # Redaction Preview
    REDACT_BLACK = "#000000"
    REDACT_WHITE = "#ffffff"
    REDACT_HIGHLIGHT = "#2563eb40"   # Semi-transparent blue for selection


# ── Font Definitions ───────────────────────────────────────────
class Fonts:
    FAMILY = "Segoe UI, SF Pro Display, -apple-system, Helvetica Neue, Arial, sans-serif"
    MONO = "JetBrains Mono, Consolas, Courier New, monospace"
    SIZE_XS = 10
    SIZE_SM = 11
    SIZE_MD = 13
    SIZE_LG = 15
    SIZE_XL = 18
    SIZE_XXL = 24


# ── Stylesheet ─────────────────────────────────────────────────
def get_stylesheet() -> str:
    return f"""
    /* ═══════════════════════════════════════════════════════
       GLOBAL
       ═══════════════════════════════════════════════════════ */
    QWidget {{
        background-color: {Colors.BG_DARKEST};
        color: {Colors.TEXT_PRIMARY};
        font-family: {Fonts.FAMILY};
        font-size: {Fonts.SIZE_MD}px;
        selection-background-color: {Colors.ACCENT};
        selection-color: {Colors.TEXT_ON_ACCENT};
    }}

    /* ═══════════════════════════════════════════════════════
       MAIN WINDOW & FRAMES
       ═══════════════════════════════════════════════════════ */
    QMainWindow {{
        background-color: {Colors.BG_DARKEST};
    }}

    QFrame#sidebar {{
        background-color: {Colors.BG_DARK};
        border-right: 1px solid {Colors.BORDER};
    }}

    QFrame#card {{
        background-color: {Colors.BG_MEDIUM};
        border: 1px solid {Colors.BORDER};
        border-radius: 8px;
        padding: 12px;
    }}

    /* ═══════════════════════════════════════════════════════
       LABELS
       ═══════════════════════════════════════════════════════ */
    QLabel {{
        background: transparent;
        border: none;
        padding: 0px;
    }}

    QLabel#title {{
        font-size: {Fonts.SIZE_XL}px;
        font-weight: 700;
        color: {Colors.TEXT_PRIMARY};
    }}

    QLabel#subtitle {{
        font-size: {Fonts.SIZE_SM}px;
        color: {Colors.TEXT_SECONDARY};
    }}

    QLabel#sectionHeader {{
        font-size: {Fonts.SIZE_MD}px;
        font-weight: 600;
        color: {Colors.ACCENT_HOVER};
        padding: 4px 0px;
    }}

    QLabel#statusLabel {{
        font-size: {Fonts.SIZE_SM}px;
        color: {Colors.TEXT_MUTED};
        padding: 4px 8px;
    }}

    /* ═══════════════════════════════════════════════════════
       BUTTONS
       ═══════════════════════════════════════════════════════ */
    QPushButton {{
        background-color: {Colors.BG_MEDIUM};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        padding: 8px 16px;
        font-size: {Fonts.SIZE_MD}px;
        font-weight: 500;
        min-height: 20px;
    }}

    QPushButton:hover {{
        background-color: {Colors.BG_LIGHT};
        border-color: {Colors.BORDER_LIGHT};
    }}

    QPushButton:pressed {{
        background-color: {Colors.BG_LIGHTER};
    }}

    QPushButton:disabled {{
        color: {Colors.TEXT_MUTED};
        background-color: {Colors.BG_DARK};
        border-color: {Colors.BORDER};
    }}

    QPushButton#primary {{
        background-color: {Colors.ACCENT};
        color: {Colors.TEXT_ON_ACCENT};
        border: none;
        font-weight: 600;
    }}

    QPushButton#primary:hover {{
        background-color: {Colors.ACCENT_HOVER};
    }}

    QPushButton#primary:pressed {{
        background-color: {Colors.ACCENT_PRESSED};
    }}

    QPushButton#primary:disabled {{
        background-color: {Colors.ACCENT_SOFT};
        color: {Colors.TEXT_MUTED};
    }}

    QPushButton#danger {{
        background-color: transparent;
        color: {Colors.ERROR};
        border: 1px solid {Colors.ERROR};
    }}

    QPushButton#danger:hover {{
        background-color: #ef44441a;
    }}

    QPushButton#small {{
        padding: 4px 10px;
        font-size: {Fonts.SIZE_SM}px;
        min-height: 16px;
    }}

    /* ═══════════════════════════════════════════════════════
       LINE EDIT / TEXT INPUT
       ═══════════════════════════════════════════════════════ */
    QLineEdit {{
        background-color: {Colors.BG_MEDIUM};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: {Fonts.SIZE_MD}px;
    }}

    QLineEdit:focus {{
        border-color: {Colors.ACCENT};
        background-color: {Colors.BG_LIGHT};
    }}

    QLineEdit:disabled {{
        color: {Colors.TEXT_MUTED};
        background-color: {Colors.BG_DARK};
    }}

    QLineEdit#searchBar {{
        font-size: {Fonts.SIZE_LG}px;
        padding: 10px 14px;
        border-radius: 8px;
        border: 2px solid {Colors.BORDER};
    }}

    QLineEdit#searchBar:focus {{
        border-color: {Colors.ACCENT};
    }}

    /* ═══════════════════════════════════════════════════════
       SCROLL AREAS
       ═══════════════════════════════════════════════════════ */
    QScrollArea {{
        border: none;
        background: transparent;
    }}

    QScrollBar:vertical {{
        background: {Colors.BG_DARK};
        width: 8px;
        margin: 0;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical {{
        background: {Colors.BG_LIGHTER};
        min-height: 30px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {Colors.ACCENT_SOFT};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background: {Colors.BG_DARK};
        height: 8px;
        margin: 0;
        border-radius: 4px;
    }}

    QScrollBar::handle:horizontal {{
        background: {Colors.BG_LIGHTER};
        min-width: 30px;
        border-radius: 4px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {Colors.ACCENT_SOFT};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* ═══════════════════════════════════════════════════════
       CHECKBOXES & RADIO BUTTONS
       ═══════════════════════════════════════════════════════ */
    QCheckBox {{
        spacing: 8px;
        color: {Colors.TEXT_PRIMARY};
        background: transparent;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {Colors.BORDER_LIGHT};
        border-radius: 4px;
        background: {Colors.BG_MEDIUM};
    }}

    QCheckBox::indicator:checked {{
        background-color: {Colors.ACCENT};
        border-color: {Colors.ACCENT};
    }}

    QCheckBox::indicator:hover {{
        border-color: {Colors.ACCENT_HOVER};
    }}

    QRadioButton {{
        spacing: 8px;
        color: {Colors.TEXT_PRIMARY};
        background: transparent;
    }}

    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {Colors.BORDER_LIGHT};
        border-radius: 9px;
        background: {Colors.BG_MEDIUM};
    }}

    QRadioButton::indicator:checked {{
        background-color: {Colors.ACCENT};
        border-color: {Colors.ACCENT};
    }}

    QRadioButton::indicator:hover {{
        border-color: {Colors.ACCENT_HOVER};
    }}

    /* ═══════════════════════════════════════════════════════
       COMBO BOX
       ═══════════════════════════════════════════════════════ */
    QComboBox {{
        background-color: {Colors.BG_MEDIUM};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        padding: 6px 12px;
        min-height: 20px;
    }}

    QComboBox:hover {{
        border-color: {Colors.BORDER_LIGHT};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {Colors.BG_MEDIUM};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER};
        selection-background-color: {Colors.ACCENT};
        selection-color: {Colors.TEXT_ON_ACCENT};
        outline: none;
    }}

    /* ═══════════════════════════════════════════════════════
       PROGRESS BAR
       ═══════════════════════════════════════════════════════ */
    QProgressBar {{
        background-color: {Colors.BG_MEDIUM};
        border: none;
        border-radius: 4px;
        text-align: center;
        color: {Colors.TEXT_PRIMARY};
        font-size: {Fonts.SIZE_SM}px;
        min-height: 8px;
        max-height: 8px;
    }}

    QProgressBar::chunk {{
        background-color: {Colors.ACCENT};
        border-radius: 4px;
    }}

    /* ═══════════════════════════════════════════════════════
       LIST WIDGET
       ═══════════════════════════════════════════════════════ */
    QListWidget {{
        background-color: {Colors.BG_MEDIUM};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        padding: 4px;
        outline: none;
    }}

    QListWidget::item {{
        background: transparent;
        color: {Colors.TEXT_PRIMARY};
        border-radius: 4px;
        padding: 6px 8px;
        margin: 1px 0px;
    }}

    QListWidget::item:selected {{
        background-color: {Colors.ACCENT_SOFT};
        color: {Colors.TEXT_PRIMARY};
    }}

    QListWidget::item:hover {{
        background-color: {Colors.BG_LIGHT};
    }}

    /* ═══════════════════════════════════════════════════════
       TAB WIDGET
       ═══════════════════════════════════════════════════════ */
    QTabWidget::pane {{
        border: 1px solid {Colors.BORDER};
        border-radius: 0 0 8px 8px;
        background: {Colors.BG_DARK};
    }}

    QTabBar::tab {{
        background: {Colors.BG_DARK};
        color: {Colors.TEXT_SECONDARY};
        border: none;
        padding: 8px 16px;
        font-weight: 500;
        border-bottom: 2px solid transparent;
    }}

    QTabBar::tab:selected {{
        color: {Colors.ACCENT_HOVER};
        border-bottom: 2px solid {Colors.ACCENT};
    }}

    QTabBar::tab:hover {{
        color: {Colors.TEXT_PRIMARY};
        background: {Colors.BG_MEDIUM};
    }}

    /* ═══════════════════════════════════════════════════════
       TOOLTIPS
       ═══════════════════════════════════════════════════════ */
    QToolTip {{
        background-color: {Colors.BG_MEDIUM};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER};
        border-radius: 4px;
        padding: 6px 10px;
        font-size: {Fonts.SIZE_SM}px;
    }}

    /* ═══════════════════════════════════════════════════════
       SPLITTER
       ═══════════════════════════════════════════════════════ */
    QSplitter::handle {{
        background-color: {Colors.BORDER};
        width: 1px;
        height: 1px;
    }}

    QSplitter::handle:hover {{
        background-color: {Colors.ACCENT};
    }}

    /* ═══════════════════════════════════════════════════════
       GROUP BOX
       ═══════════════════════════════════════════════════════ */
    QGroupBox {{
        font-weight: 600;
        color: {Colors.ACCENT_HOVER};
        border: 1px solid {Colors.BORDER};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 16px;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 2px 10px;
        background-color: {Colors.BG_DARK};
    }}

    /* ═══════════════════════════════════════════════════════
       MESSAGE BOX
       ═══════════════════════════════════════════════════════ */
    QMessageBox {{
        background-color: {Colors.BG_DARK};
    }}

    QMessageBox QLabel {{
        color: {Colors.TEXT_PRIMARY};
    }}

    /* ═══════════════════════════════════════════════════════
       DROP ZONE (custom)
       ═══════════════════════════════════════════════════════ */
    QFrame#dropZone {{
        background-color: {Colors.BG_MEDIUM};
        border: 2px dashed {Colors.BORDER_LIGHT};
        border-radius: 12px;
    }}

    QFrame#dropZone:hover {{
        border-color: {Colors.ACCENT};
        background-color: {Colors.BG_LIGHT};
    }}
    """


def apply_theme(app: QApplication) -> None:
    """Apply the premium dark theme to the entire application."""
    app.setStyleSheet(get_stylesheet())

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(Colors.BG_DARKEST))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(Colors.BG_MEDIUM))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(Colors.BG_DARK))
    palette.setColor(QPalette.ColorRole.Text, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(Colors.BG_MEDIUM))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(Colors.ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(Colors.TEXT_ON_ACCENT))
    app.setPalette(palette)
