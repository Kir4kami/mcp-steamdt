"""Setup script for SteamDT MCP (for git+ install only, not for PyPI publishing)."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="steamdt-mcp",
    version="0.1.0",
    description="SteamDT MCP server for querying CS2 item prices and market data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Kir4kami",
    author_email="kir4kami@users.noreply.github.com",
    url="https://github.com/Kir4kami/mcp-steamdt",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "steamdt-mcp=steamdt_mcp.server:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

