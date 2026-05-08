"""Outil de déploiement du monorepo Alfaco vers Sublime Text Packages/."""
from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path


def detect_packages_dir() -> Path:
    """Retourne le chemin du dossier Packages/ de Sublime Text.

    Ordre de résolution :
    1. Variable d'environnement SUBLIME_PACKAGES_DIR.
    2. Détection automatique selon l'OS / WSL.
    """
    env = os.environ.get("SUBLIME_PACKAGES_DIR")
    if env:
        return Path(env).expanduser()

    system = platform.system()
    if system == "Linux":
        if _is_wsl():
            user = os.environ.get("USER") or os.environ.get("USERNAME")
            if not user:
                raise RuntimeError(
                    "WSL détecté mais USER non défini. "
                    "Posez SUBLIME_PACKAGES_DIR=/mnt/c/Users/<user>/AppData/Roaming/Sublime Text/Packages"
                )
            return Path(f"/mnt/c/Users/{user}/AppData/Roaming/Sublime Text/Packages")
        st4 = Path.home() / ".config/sublime-text/Packages"
        st3 = Path.home() / ".config/sublime-text-3/Packages"
        return st4 if st4.exists() else st3
    if system == "Darwin":
        return Path.home() / "Library/Application Support/Sublime Text/Packages"
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise RuntimeError("APPDATA non défini sur Windows")
        return Path(appdata) / "Sublime Text/Packages"
    raise RuntimeError(f"OS non supporté : {system}")


def _is_wsl() -> bool:
    """Retourne True si l'environnement courant est WSL."""
    if not sys.platform.startswith("linux"):
        return False
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except OSError:
        return False
