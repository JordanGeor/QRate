import sqlite3
from pathlib import Path

from app.db import engine


def get_sqlite_path() -> Path:
    url = str(engine.url)  # π.χ. sqlite:///C:/Users/.../data/app.db
    if not url.startswith("sqlite:///"):
        raise RuntimeError(f"Not a sqlite database url: {url}")

    path_str = url.replace("sqlite:///", "", 1)

    # Windows path μπορεί να έρθει με /, το Path το χειρίζεται.
    return Path(path_str)


def main():
    db_path = get_sqlite_path()
    print("DB PATH:", db_path)

    if not db_path.exists():
        raise FileNotFoundError(f"DB file not found: {db_path}")

    con = sqlite3.connect(str(db_path))
    cur = con.cursor()

    # check table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contact_requests';")
    if not cur.fetchone():
        print("ERROR: table contact_requests does not exist in DB.")
        print("Existing tables:")
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        print([r[0] for r in cur.fetchall()])
        con.close()
        return

    # check columns
    cur.execute("PRAGMA table_info(contact_requests)")
    cols = [r[1] for r in cur.fetchall()]
    print("cols before:", cols)

    if "is_read" not in cols:
        cur.execute("ALTER TABLE contact_requests ADD COLUMN is_read INTEGER NOT NULL DEFAULT 0;")
        con.commit()
        print("OK: added is_read")
    else:
        print("OK: is_read already exists")

    # optional index
    cur.execute("CREATE INDEX IF NOT EXISTS ix_contact_requests_is_read ON contact_requests (is_read);")
    con.commit()

    cur.execute("PRAGMA table_info(contact_requests)")
    print("cols after:", [r[1] for r in cur.fetchall()])

    con.close()
    print("DONE")


if __name__ == "__main__":
    main()
