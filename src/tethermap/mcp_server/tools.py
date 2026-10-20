from contextlib import contextmanager
from typing import  Annotated

from pydantic import Field

from tethermap.core.db import connect
from tethermap.core.graph import GraphStore
from tethermap.core.models import EdgeKind, NodeKind, Origin

Name = Annotated[str, Field(pattern=r"^[A-Za-z0-9._-]{1,100}$")]

@contextmanager
def graph():
    with connect() as conn:
        yield GraphStore(conn)


def get_service_relationships(name: Name) -> dict:
    """List what a service provides, consumes, and what else, points at it."""
    with graph() as g:
        return {"service": name, "relationship": g.get_relationships(NodeKind.SERVICE, name)}


def register_service(
        name: Name,
        provides: list[Name] | None = None,
        consumes: list[Name] | None = None,
) -> dict:
    """Register a service and the contracts it provides or consumes. Declared links are marked confirmed."""
    provides = provides or []
    consumes = consumes or []
    with graph() as g:
        service = g.upsert_node(NodeKind.SERVICE, name)
        for contract, edge in [(c, EdgeKind.PROVIDES) for c in provides] + [
            (c, EdgeKind.CONSUMES) for c in consumes
        ]:
            g.add_edge(service, g.upsert_node(NodeKind.CONTRACT, contract), edge, Origin.CONFIRMED)
        return {"service": name, "version": service.version, "provides": provides, "consumes": consumes}


READ_TOOLS = [get_service_relationships]
WRITE_TOOLS = [register_service]