import os


def get_db_url():
    DB_URL = os.getenv("DB_URL")

    if DB_URL:
        return DB_URL

    PGPORT = os.getenv("PGPORT") or ""
    PGDATABASE = os.getenv("PGDATABASE") or ""
    PGHOST = os.getenv("PGHOST") or ""
    PGUSER = os.getenv("PGUSER") or ""
    PGPASSWORD = os.getenv("PGPASSWORD") or ""
    DB_EXTRAS = os.getenv("DB_EXTRAS") or ""
    url = (
        f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}{DB_EXTRAS}"
    )
    return url
