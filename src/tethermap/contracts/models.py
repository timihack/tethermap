from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldSpec:
    type: str | None
    required: bool
    enum: frozenset[str] | None = None


@dataclass
class Operation:
    request: dict[str, FieldSpec] = field(default_factory=dict)
    responses: dict[str, dict[str, FieldSpec]] = field(default_factory=dict)


@dataclass
class Contract:
    operations: dict[str, Operation]
