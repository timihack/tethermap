import os
from pathlib import Path

import psycopg
from psycopg.rows import DictRow, dict_row

SCHEMA_FILE = Path(__file__).with_name("schema.sql")
DEFAULT_URL = "postgresql://tethermap:tethermap@localhost:5433/tethermap"


def connect() -> psycopg.Connection[DictRow]:
    url = os.getenv("DATABASE_URL", DEFAULT_URL)
    return psycopg.Connection[DictRow].connect(url, row_factory=dict_row, autocommit=True)


def init_schema(conn: psycopg.Connection[DictRow]) -> None:
    conn.execute(SCHEMA_FILE.read_bytes())