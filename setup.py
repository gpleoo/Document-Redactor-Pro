from setuptools import setup, find_packages

setup(
    name="ai-document-redactor-pro",
    version="1.0.0",
    description="AI Document Redactor Pro - Offline document redaction tool",
    author="AI Document Redactor Pro Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "PyQt6>=6.6.0",
        "pymupdf>=1.23.0",
        "Pillow>=10.0.0",
        "pytesseract>=0.3.10",
        "spacy>=3.7.0",
        "presidio-analyzer>=2.2.0",
        "presidio-anonymizer>=2.2.0",
        "cryptography>=41.0.0",
    ],
    entry_points={
        "console_scripts": [
            "redactor-pro=main:main",
        ],
    },
)
