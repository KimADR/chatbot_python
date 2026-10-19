from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Sauvegarder une base SQLite Orinasa de manière cohérente")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()

    source = args.source.expanduser()
    destination = args.destination.expanduser()
    if not source.exists():
        raise SystemExit(f"Base introuvable : {source}")
    if destination.exists():
        raise SystemExit(f"Le fichier existe déjà : {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(source) as src, sqlite3.connect(destination) as dst:
        src.backup(dst)
        result = dst.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        destination.unlink(missing_ok=True)
        raise SystemExit(f"Contrôle d'intégrité échoué : {result}")
    print(destination)


if __name__ == "__main__":
    main()
