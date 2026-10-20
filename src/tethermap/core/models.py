from dataclasses import dataclass
from enum import StrEnum

class NodeKind(StrEnum):
  SERVICE = "service"
  CONTRACT = "contract"
  ENDPOINT = "endpoint"
  TEST = "test"
  DEPLOYMENT = "deployment"


class EdgeKind(StrEnum):
  PROVIDES = "provides"
  CONSUMES = "consumes"
  COVERS = "covers"
  DEPLOYED_AS = "deployed_as"


class Origin(StrEnum):
  CONFIRMED = "confirmed"
  INFERRED = "inferred"


@dataclass(frozen=True)
class Node:
  id: int
  kind: NodeKind
  name: str
  attributes: dict
  version: int