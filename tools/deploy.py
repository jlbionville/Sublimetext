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
            user = (
                _windows_username_from_wsl()
                or os.environ.get("USER")
                or os.environ.get("USERNAME")
            )
            if not user:
                raise RuntimeError(
                    "WSL détecté mais aucun nom d'utilisateur Windows résolu. "
                    "Posez SUBLIME_PACKAGES_DIR=/mnt/c/Users/<user>/AppData/Roaming/Sublime Text/Packages"
                )
            candidate = Path(
                f"/mnt/c/Users/{user}/AppData/Roaming/Sublime Text/Packages"
            )
            user_profile = Path(f"/mnt/c/Users/{user}")
            if not user_profile.exists():
                raise RuntimeError(
                    f"Profil Windows '{user}' introuvable sous /mnt/c/Users/. "
                    "Posez SUBLIME_PACKAGES_DIR pour pointer manuellement vers votre dossier Packages Sublime."
                )
            return candidate
        xdg = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        st4 = xdg / "sublime-text/Packages"
        st3 = xdg / "sublime-text-3/Packages"
        if st4.exists():
            return st4
        if st3.exists():
            return st3
        return st4  # fresh install : default to ST4 (current major version)
    if system == "Darwin":
        return Path.home() / "Library/Application Support/Sublime Text/Packages"
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise RuntimeError("APPDATA non défini sur Windows")
        return Path(appdata) / "Sublime Text/Packages"
    raise RuntimeError(f"OS non supporté : {system}")


def _is_wsl() -> bool:
    """Retourne True si l'environnement courant est WSL.

    Vérifie en cascade :
    1. Variables d'environnement WSL_DISTRO_NAME / WSL_INTEROP (les plus fiables).
    2. /proc/version et /proc/sys/kernel/osrelease (contiennent 'microsoft').
    """
    if not sys.platform.startswith("linux"):
        return False
    if os.environ.get("WSL_DISTRO_NAME") or os.environ.get("WSL_INTEROP"):
        return True
    for path in ("/proc/version", "/proc/sys/kernel/osrelease"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                if "microsoft" in f.read().lower():
                    return True
        except OSError:
            continue
    return False


def _windows_username_from_wsl():
    """Best-effort lookup of the host Windows username from WSL.

    Retourne le nom d'utilisateur Windows en string, ou None si cmd.exe
    n'est pas joignable. Permet de gérer le cas où le nom d'utilisateur
    Linux (ex: 'ubuntu') diffère du nom d'utilisateur Windows.
    """
    try:
        import subprocess
        out = subprocess.check_output(
            ["/mnt/c/Windows/System32/cmd.exe", "/c", "echo %USERNAME%"],
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).decode("utf-8", errors="ignore").strip()
        return out or None
    except (OSError, subprocess.SubprocessError):
        return None
