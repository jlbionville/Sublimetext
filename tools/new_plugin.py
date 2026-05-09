"""Scaffold un nouveau plugin Alfaco depuis tools/templates/plugin/."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def render_template(src: Path, dst: Path, name: str) -> None:
    name_lower = name.lower()
    if dst.exists():
        raise FileExistsError(f"{dst} existe déjà")
    shutil.copytree(src, dst)
    for path in dst.rglob("*"):
        if path.is_file():
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            content = content.replace("{{NAME}}", name).replace("{{name}}", name_lower)
            path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(prog="new-plugin")
    parser.add_argument("name", help="Nom du plugin sans préfixe (ex: Git → AlfacoGit)")
    args = parser.parse_args()

    monorepo_root = Path(__file__).resolve().parents[1]
    template = monorepo_root / "tools" / "templates" / "plugin"
    target = monorepo_root / "plugins" / f"Alfaco{args.name}"
    render_template(template, target, args.name)
    print(f"Plugin créé : {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
