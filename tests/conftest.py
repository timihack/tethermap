import pytest

from tethermap.core.db import connect, init_schema
from tethermap.core.graph import GraphStore


@pytest.fixture
def store():
    with connect() as conn:
        init_schema(conn)
        conn.execute("TRUNCATE nodes CASCADE")
        yield GraphStore(conn)