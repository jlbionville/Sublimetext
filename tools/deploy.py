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


EXCLUDE_DURING_DEPLOY = {
    "tests", "__pycache__", ".pytest_cache", ".git", "templates",
    # Marqueur Package Control « ce paquet est géré par moi » : s'il est présent
    # et que le plugin n'est pas dans installed_packages, PC le supprime au
    # démarrage de Sublime. On préfère que PC les ignore comme tout dossier manuel.
    "package-metadata.json",
}


def _iter_plugins(monorepo_root: Path) -> list[Path]:
    plugins_dir = monorepo_root / "plugins"
    return sorted(p for p in plugins_dir.iterdir() if p.is_dir() and not p.name.startswith("."))


def _filter_for_deploy(src: Path, name: str) -> bool:
    if name in EXCLUDE_DURING_DEPLOY:
        return False
    if name.endswith(".pyc"):
        return False
    return True


def _copy_plugin(src: Path, dst: Path) -> None:
    if dst.exists():
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=lambda d, names: [n for n in names if not _filter_for_deploy(Path(d), n)])


def _link_plugin(src: Path, dst: Path) -> None:
    if dst.exists() or dst.is_symlink():
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    try:
        os.symlink(src, dst, target_is_directory=True)
    except (OSError, NotImplementedError):
        # Fallback Windows : junction
        if platform.system() == "Windows":
            os.system(f'mklink /J "{dst}" "{src}"')
        else:
            raise


def link(monorepo_root: Path, packages_dir: Path, only: str | None = None) -> list[str]:
    if _is_wsl():
        print("WSL détecté → mode 'install' (copie) forcé : NTFS ne suit pas les symlinks WSL.")
        return install(monorepo_root, packages_dir, only=only)
    done = []
    for plugin in _iter_plugins(monorepo_root):
        if only and plugin.name != only:
            continue
        _link_plugin(plugin, packages_dir / plugin.name)
        done.append(plugin.name)
    return done


def install(monorepo_root: Path, packages_dir: Path, only: str | None = None) -> list[str]:
    done = []
    for plugin in _iter_plugins(monorepo_root):
        if only and plugin.name != only:
            continue
        _copy_plugin(plugin, packages_dir / plugin.name)
        done.append(plugin.name)
    return done


def uninstall(monorepo_root: Path, packages_dir: Path, only: str | None = None) -> list[str]:
    done = []
    for plugin in _iter_plugins(monorepo_root):
        if only and plugin.name != only:
            continue
        dst = packages_dir / plugin.name
        if not dst.exists() and not dst.is_symlink():
            continue
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
        done.append(plugin.name)
    return done


def init_config(monorepo_root: Path, packages_dir: Path, only: str | None = None,
                force: bool = False) -> list[tuple[str, str, str]]:
    """Copie les templates plugins/<X>/templates/User/* vers <Packages>/User/.

    Ne remplace PAS un fichier existant (sauf `force=True`) — on ne veut
    jamais écraser une config utilisateur déjà remplie. Retourne la liste
    des opérations sous la forme (action, plugin, filename) où action vaut
    'copied' ou 'skipped'.
    """
    user_dir = packages_dir / "User"
    user_dir.mkdir(parents=True, exist_ok=True)
    done: list[tuple[str, str, str]] = []
    for plugin in _iter_plugins(monorepo_root):
        if only and plugin.name != only:
            continue
        template_dir = plugin / "templates" / "User"
        if not template_dir.is_dir():
            continue
        for template in sorted(template_dir.iterdir()):
            if not template.is_file():
                continue
            dst = user_dir / template.name
            if dst.exists() and not force:
                done.append(("skipped", plugin.name, template.name))
                continue
            shutil.copy2(template, dst)
            done.append(("copied", plugin.name, template.name))
    return done


def status(monorepo_root: Path, packages_dir: Path) -> dict[str, str]:
    out = {}
    for plugin in _iter_plugins(monorepo_root):
        dst = packages_dir / plugin.name
        if not dst.exists() and not dst.is_symlink():
            out[plugin.name] = "absent"
        elif dst.is_symlink():
            out[plugin.name] = "link"
        else:
            out[plugin.name] = "copy"
    return out


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="deploy")
    parser.add_argument("action", choices=["link", "install", "uninstall", "status", "init-config"])
    parser.add_argument("--plugin", default=None, help="Cibler un seul plugin")
    parser.add_argument("--packages-dir", default=None)
    parser.add_argument("--force", action="store_true",
                        help="(init-config) écrase un fichier User/ existant")
    args = parser.parse_args()

    monorepo_root = Path(__file__).resolve().parents[1]
    packages_dir = Path(args.packages_dir).expanduser() if args.packages_dir else detect_packages_dir()

    if args.action == "status":
        for name, mode in status(monorepo_root, packages_dir).items():
            print(f"  {name:25s} {mode}")
        return 0
    if args.action == "init-config":
        ops = init_config(monorepo_root, packages_dir, only=args.plugin, force=args.force)
        if not ops:
            print("init-config : aucun template trouvé.")
            return 0
        for action, plugin, fname in ops:
            print(f"  [{action:7s}] {plugin}: {fname}")
        copied = sum(1 for a, _, _ in ops if a == "copied")
        skipped = sum(1 for a, _, _ in ops if a == "skipped")
        print(f"init-config : {copied} copié(s), {skipped} ignoré(s) (déjà présent — utiliser --force pour écraser).")
        return 0
    if args.action == "link":
        done = link(monorepo_root, packages_dir, only=args.plugin)
    elif args.action == "install":
        done = install(monorepo_root, packages_dir, only=args.plugin)
    elif args.action == "uninstall":
        done = uninstall(monorepo_root, packages_dir, only=args.plugin)
    else:
        return 2
    print(f"{args.action}: {len(done)} plugin(s) → {', '.join(done) or '(aucun)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
