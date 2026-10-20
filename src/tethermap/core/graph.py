import psycopg
from psycopg.rows import DictRow
from psycopg.types.json import Jsonb

from tethermap.core.models import EdgeKind, Node, NodeKind, Origin

class GraphStore:
    def __init__(self, conn: psycopg.Connection[DictRow]):
        self.conn = conn

    def upsert_node(self, kind: NodeKind, name: str, attributes: dict | None = None) -> Node:
        attributes = attributes or {}
        with self.conn.transaction():
            row = self.conn.execute(
                """
                INSERT INTO nodes (kind, name, attributes) VALUES (%s, %s, %s)
                ON CONFLICT (kind, name) DO UPDATE
                SET attributes = EXCLUDED.attributes,
                    version = nodes.version + 1,
                    updated_at = now()
                WHERE nodes.attributes IS DISTINCT FROM EXCLUDED.attributes
                RETURNING id, kind, name, attributes, version
                """,
                (kind, name, Jsonb(attributes)),
            ).fetchone()
            if row is not None:
                self.conn.execute(
                    "INSERT INTO node_versions (node_id, version, attributes) VALUES (%s, %s, %s)",
                    (row["id"], row["version"], Jsonb(row["attributes"])),
                )
        if row is None:
            return self.get_node(kind, name)
        return Node(**row)

    def get_node(self, kind: NodeKind, name: str) -> Node:
        row = self.conn.execute(
            "SELECT id, kind, name, attributes, version FROM nodes WHERE kind = %s AND name = %s",
            (kind, name),
        ).fetchone()
        if row is None:
            raise LookupError(f"{kind} '{name}' not found")
        return Node(**row)

    def add_edge(self, source: Node, target: Node, kind: EdgeKind, origin: Origin) -> None:
        self.conn.execute(
            """
            INSERT INTO edges (source_id, target_id, kind, origin) VALUES (%s, %s, %s, %s)
            ON CONFLICT (source_id, target_id, kind) DO UPDATE SET origin = EXCLUDED.origin
            """,
            (source.id, target.id, kind, origin),
        )

    def get_relationships(self, kind: NodeKind, name: str) -> list[DictRow]:
        node = self.get_node(kind, name)
        return self.conn.execute(
            """
            SELECT 'outgoing' AS direction, e.kind AS edge, e.origin, n.kind AS node_kind, n.name AS node_name
            FROM edges e JOIN nodes n ON n.id = e.target_id
            WHERE e.source_id = %(id)s
            UNION ALL
            SELECT 'incoming', e.kind, e.origin, n.kind, n.name
            FROM edges e JOIN nodes n ON n.id = e.source_id
            WHERE e.target_id = %(id)s
            ORDER BY direction, edge, node_name
            """,
            {"id": node.id},
        ).fetchall()