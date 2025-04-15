#!/usr/bin/env python
"""
Setup script for ViGCA
"""
import os
from setuptools import setup, find_packages

# Get the long description from README.md
with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md'), 
          encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="vigca",
    version="0.1.0",
    description="Vision-Guided Cursor Automation - AI program to control the cursor based on visual targets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/your-username/vigca",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.19.0",
        "opencv-python>=4.5.0",
        "mss>=6.0.0",
        "pyautogui>=0.9.50",
        "pillow>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "vigca=vigca.main:main",
        ],
    },
    keywords="automation, computer-vision, cursor-control, ai, image-recognition",
    project_urls={
        "Bug Reports": "https://github.com/your-username/vigca/issues",
        "Source": "https://github.com/your-username/vigca",
    },
    include_package_data=True,
)