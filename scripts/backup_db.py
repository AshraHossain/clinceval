"""SQLite online backup (safe while the app is running).

Usage: python scripts/backup_db.py [dest_dir]
Cron example (nightly 02:00): 0 2 * * * cd /path/to/clinceval && python scripts/backup_db.py backups/
"""
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "eval" / "eval_results.db"


def backup(db_path: Path = DB_PATH, dest_dir: Path | None = None) -> Path:
    dest_dir = dest_dir or (BASE_DIR / "backups")
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = dest_dir / f"eval_results_{stamp}.db"

    source = sqlite3.connect(db_path)
    target = sqlite3.connect(dest)
    with target:
        source.backup(target)  # uses SQLite's online backup API — consistent snapshot
    source.close()
    target.close()
    return dest


if __name__ == "__main__":
    dest_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    print(f"Backed up to {backup(dest_dir=dest_dir)}")
