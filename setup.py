#!/usr/bin/env python3
"""
Setup script para agent-isa con integración de Manus.
"""

from setuptools import setup, find_packages
import os

# Leer README.md para la descripción larga
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Leer requisitos base
with open("requirements/core.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

# Definir extras_require para módulos opcionales
extras_require = {}

# Leer requisitos de módulos opcionales
for module in ["search", "content", "image", "code", "filesystem", "distribution", "dev"]:
    req_file = f"requirements/{module}.txt"
    if os.path.exists(req_file):
        with open(req_file, "r", encoding="utf-8") as f:
            extras_require[module] = f.read().splitlines()

# Definir "all" para instalar todos los módulos opcionales
extras_require["all"] = [req for module_reqs in extras_require.values() for req in module_reqs]

setup(
    name="agent-isa-manus",
    version="0.1.0",
    author="Jorge Grisales",
    author_email="jivagrisma@gmail.com",
    description="Agent-ISA con integración de habilidades de Manus",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jivagrisma/agent-isa",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "agent-isa=OpenManusWeb.cli:main",
        ],
    },
    include_package_data=True,
)
