"""
File Manager - Handles file I/O and temporary copies.
Original file is NEVER modified.
"""

import os
import shutil
import tempfile
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


class FileManager:

    def __init__(self):
        self._original_path = None
        self._temp_dir = None
        self._working_copy = None

    @property
    def original_path(self):
        return self._original_path

    @property
    def working_copy(self):
        return self._working_copy

    @property
    def original_name(self) -> str:
        return Path(self._original_path).stem if self._original_path else "document"

    @property
    def is_pdf(self) -> bool:
        if self._original_path:
            return Path(self._original_path).suffix.lower() == ".pdf"
        return False

    @staticmethod
    def is_supported(path: str) -> bool:
        return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS

    def load_file(self, file_path: str) -> str | None:
        src = Path(file_path)
        if not src.exists() or not self.is_supported(file_path):
            return None
        self.cleanup()
        self._original_path = str(src)
        self._temp_dir = tempfile.mkdtemp(prefix="redactor_")
        dest = Path(self._temp_dir) / src.name
        shutil.copy2(str(src), str(dest))
        self._working_copy = str(dest)
        return self._working_copy

    def get_export_path(self) -> str:
        parent = Path(self._original_path).parent if self._original_path else Path.home()
        return str(parent / f"{self.original_name}_REDACTED.pdf")

    def cleanup(self):
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        self._temp_dir = None
        self._working_copy = None
        self._original_path = None
