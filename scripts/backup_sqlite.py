from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = Path(os.getenv("ORINASA_DB_PATH", root / "data" / "orinasa.sqlite"))
if not src.exists():
    raise SystemExit(f"Base introuvable: {src}")
out_dir = root / "backups"
out_dir.mkdir(exist_ok=True)
target = out_dir / f"orinasa_{datetime.now():%Y%m%d_%H%M%S}.sqlite"
shutil.copy2(src, target)
print(target)
