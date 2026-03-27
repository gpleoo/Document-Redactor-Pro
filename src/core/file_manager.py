"""
File Manager Module - Handles file I/O, temporary copies, and export paths.
Ensures the original file is never modified.
"""

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


class FileManager:
    """Manages file operations: loading, temporary copies, and export.

    Guarantees that the original file is never modified by always
    working on temporary copies.
    """

    def __init__(self):
        self._original_path: Optional[Path] = None
        self._temp_dir: Optional[str] = None
        self._working_copy: Optional[Path] = None

    @property
    def original_path(self) -> Optional[Path]:
        return self._original_path

    @property
    def working_copy(self) -> Optional[Path]:
        return self._working_copy

    @property
    def original_filename(self) -> str:
        if self._original_path:
            return self._original_path.stem
        return "document"

    @property
    def original_extension(self) -> str:
        if self._original_path:
            return self._original_path.suffix.lower()
        return ".pdf"

    @property
    def is_pdf(self) -> bool:
        return self.original_extension == ".pdf"

    @property
    def is_image(self) -> bool:
        return self.original_extension in {".jpg", ".jpeg", ".png"}

    @staticmethod
    def is_supported(file_path: str) -> bool:
        """Check if a file has a supported extension."""
        return Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS

    def load_file(self, file_path: str) -> Optional[str]:
        """Load a file by creating a temporary working copy.

        Returns the path to the working copy, or None on failure.
        The original file is never touched after this copy.
        """
        src = Path(file_path)
        if not src.exists():
            logger.error(f"File not found: {file_path}")
            return None

        if not self.is_supported(file_path):
            logger.error(f"Unsupported file type: {src.suffix}")
            return None

        self.cleanup()

        self._original_path = src
        self._temp_dir = tempfile.mkdtemp(prefix="redactor_")
        dest = Path(self._temp_dir) / src.name
        shutil.copy2(str(src), str(dest))
        self._working_copy = dest

        logger.info(f"Created working copy: {dest}")
        return str(dest)

    def get_default_export_name(self) -> str:
        """Generate the default export filename: [OriginalName]_REDACTED.pdf"""
        return f"{self.original_filename}_REDACTED.pdf"

    def get_default_export_path(self) -> str:
        """Generate the default full export path in the original file's directory."""
        if self._original_path:
            parent = self._original_path.parent
        else:
            parent = Path.home() / "Documents"
        return str(parent / self.get_default_export_name())

    def export_file(self, source_path: str, destination_path: str) -> bool:
        """Copy the processed file to the user-selected destination."""
        try:
            dest = Path(destination_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, str(dest))
            logger.info(f"Exported to: {destination_path}")
            return True
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False

    def cleanup(self):
        """Remove temporary files and directories."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
                logger.info(f"Cleaned up temp directory: {self._temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp dir: {e}")
        self._temp_dir = None
        self._working_copy = None
        self._original_path = None

    def __del__(self):
        self.cleanup()
