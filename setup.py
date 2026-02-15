"""EasyPdfForYou - A lightweight PDF document processing and translation tool."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="easypdfforyou",
    version="0.1.0",
    author="Guillaume Leone",
    author_email="GuillaumeLeone8@gmail.com",
    description="A lightweight PDF document processing and translation tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GuillaumeLeone8/EasyPdfForYou",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyMuPDF>=1.23.0",
        "Pillow>=10.0.0",
        "pytesseract>=0.3.10",
        "googletrans>=4.0.0",
        "requests>=2.31.0",
        "flask>=2.3.0",
        "click>=8.0.0",
        "reportlab>=4.0.0",
        "numpy>=1.24.0",
        "opencv-python>=4.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "epdf=easypdfforyou.cli.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "easypdfforyou": ["web/templates/*.html", "web/static/*"],
    },
)