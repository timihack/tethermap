import pytest

from tethermap.core.models import EdgeKind, NodeKind, Origin


def test_upsert_bumps_version_only_when_attributes_change(store):
    first = store.upsert_node(NodeKind.SERVICE, "orders", {"team": "a"})
    same = store.upsert_node(NodeKind.SERVICE, "orders", {"team": "a"})
    changed = store.upsert_node(NodeKind.SERVICE, "orders", {"team": "b"})
    assert (first.version, same.version, changed.version) == (1, 1, 2)
    rows = store.conn.execute("SELECT version FROM node_versions WHERE node_id = %s ORDER BY version", (first.id,)).fetchall()
    assert [r["version"] for r in rows] == [1, 2]


def test_relationships_show_both_directions(store):
    orders = store.upsert_node(NodeKind.SERVICE, "orders")
    billing = store.upsert_node(NodeKind.SERVICE, "billing")
    contract = store.upsert_node(NodeKind.CONTRACT, "orders-api")
    store.add_edge(orders, contract, EdgeKind.PROVIDES, Origin.CONFIRMED)
    store.add_edge(billing, contract, EdgeKind.CONSUMES, Origin.INFERRED)

    assert store.get_relationships(NodeKind.SERVICE, "orders") == [
        {"direction": "outgoing", "edge": "provides", "origin": "confirmed", "node_kind": "contract", "node_name": "orders-api"}
    ]
    incoming = store.get_relationships(NodeKind.CONTRACT, "orders-api")
    assert [(r["direction"], r["edge"], r["origin"], r["node_name"]) for r in incoming] == [
        ("incoming", "consumes", "inferred", "billing"),
        ("incoming", "provides", "confirmed", "orders"),
    ]


def test_missing_node_raises(store):
    with pytest.raises(LookupError):
        store.get_relationships(NodeKind.SERVICE, "ghost")