#!/usr/bin/env python3
"""Setup script for AI Utilities."""

from setuptools import setup, find_packages

setup(
    name="ai_utilities",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pydantic>=2.0.0",
        "requests>=2.25.0",
        "python-dotenv>=0.19.0",
        "openai>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-mock>=3.8.0",
            "pytest-json-report>=1.5.0",
            "psutil>=5.8.0",
        ],
        "audio": [
            "openai-whisper>=20230314",
            "pydub>=0.25.0",
        ],
    },
    python_requires=">=3.8",
)
