"""
Setup configuration for Memori package
"""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
def read_requirements(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="memoriai",
    version="0.1.0",
    author="Memori Team",
    author_email="contact@memoriai.dev",
    description="The Open-Source Memory Layer for AI Agents & Multi-Agent Systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/memoriai",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
        "postgres": ["psycopg2-binary"],
        "mysql": ["PyMySQL"],
    },
    entry_points={
        "console_scripts": [
            "memori=memoriai.cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/memoriai/issues",
        "Source": "https://github.com/yourusername/memoriai",
        "Documentation": "https://memoriai.readthedocs.io",
    },
)

