from __future__ import annotations

import argparse
import os
from pathlib import Path

import uvicorn


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lancer Orinasa")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--demo", action="store_true", help="Démonstration modifiable avec données fictives")
    mode.add_argument("--empty", action="store_true", help="Atelier vide sans équipements ni incidents préchargés")
    parser.add_argument("--read-only", action="store_true", help="Interdire les écritures métier")
    parser.add_argument("--data-dir", type=Path, help="Dossier des bases SQLite")
    parser.add_argument("--host", default="127.0.0.1", help="Adresse d'écoute")
    parser.add_argument("--port", type=int, default=8000, help="Port HTTP")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    demo = not args.empty
    if args.demo:
        demo = True
    os.environ["ORINASA_DEMO"] = "1" if demo else "0"
    if args.read_only:
        os.environ["ORINASA_READ_ONLY"] = "1"
    if args.data_dir:
        os.environ["ORINASA_DATA_DIR"] = str(args.data_dir.expanduser().resolve())

    token = os.getenv("ORINASA_API_TOKEN", "")
    if args.host == "0.0.0.0" and not token and not (demo and args.read_only):
        raise SystemExit("Refus de l'écoute sur 0.0.0.0 sans ORINASA_API_TOKEN, sauf démonstration fictive en lecture seule.")

    from .app import create_app

    app = create_app(seed_demo=demo)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
