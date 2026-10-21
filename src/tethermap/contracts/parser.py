from pathlib import Path
from typing import Any

import yaml

from tethermap.contracts.models import Contract, FieldSpec, Operation

METHODS = {"get", "put", "post", "delete", "patch", "head", "options"}


def load_contract(path: str | Path) -> Contract:
    spec = yaml.safe_load(Path(path).read_text())
    if not isinstance(spec, dict):
        raise ValueError("Not an OpenAPI document")
    version = str(spec.get("openapi", ""))
    if not version.startswith(("3.0", "3.1")):
        raise ValueError(f"Unsupported OpenAPI version: {version or 'missing'}")
    operations = {}
    for url, item in spec.get("paths", {}).items():
        for method, raw in item.items():
            if method in METHODS:
                operations[f"{method.upper()} {url}"] = build_operation(spec, item.get("parameters", []), raw)
    return Contract(operations)


def build_operation(spec: dict, shared_params: list, raw: dict) -> Operation:
    operation = Operation()
    for param in [*shared_params, *raw.get("parameters", [])]:
        param, seen = deref(spec, param, ())
        flatten(spec, param.get("schema", {}), f"{param['in']}.{param['name']}", param.get("required", False), seen, operation.request)
    body, _ = deref(spec, raw.get("requestBody", {}), ())
    schema = pick_schema(body.get("content"))
    if schema is not None:
        flatten(spec, schema, "body", body.get("required", False), (), operation.request)
    for status, response in raw.get("responses", {}).items():
        response, _ = deref(spec, response, ())
        fields: dict[str, FieldSpec] = {}
        schema = pick_schema(response.get("content"))
        if schema is not None:
            flatten(spec, schema, "body", True, (), fields)
        operation.responses[str(status)] = fields
    return operation


def pick_schema(content: dict | None) -> dict | None:
    if not content:
        return None
    media = content.get("application/json") or next(iter(content.values()))
    return media.get("schema")


def deref(spec: dict, node: Any, seen: tuple[str, ...]) -> tuple[dict, tuple[str, ...]]:
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if not ref.startswith("#/"):
            raise ValueError(f"Only local references are supported: {ref}")
        if ref in seen:
            return {}, seen
        seen = (*seen, ref)
        node = spec
        for part in ref[2:].split("/"):
            node = node[part.replace("~1", "/").replace("~0", "~")]
    return (node if isinstance(node, dict) else {}), seen


def merge_all_of(spec: dict, schema: object, seen: tuple[str, ...]) -> tuple[dict, tuple[str, ...]]:
    schema, seen = deref(spec, schema, seen)
    result = {key: value for key, value in schema.items() if key != "allOf"}
    for part in schema.get("allOf", []):
        sub, _ = merge_all_of(spec, part, seen)
        result["properties"] = {**sub.get("properties", {}), **result.get("properties", {})}
        result["required"] = [*sub.get("required", []), *result.get("required", [])]
        for key in ("type", "enum", "items"):
            if key in sub:
                result.setdefault(key, sub[key])
    return result, seen


def flatten(spec: dict, schema: object, path: str, required: bool, seen: tuple[str, ...], out: dict[str, FieldSpec]) -> None:
    schema, seen = merge_all_of(spec, schema, seen)
    type_ = schema.get("type")
    if isinstance(type_, list):
        type_ = next((t for t in type_ if t != "null"), None)
    enum = frozenset(map(str, schema["enum"])) if "enum" in schema else None
    out[path] = FieldSpec(type_, required, enum)
    required_names = set(schema.get("required", []))
    for name, child in schema.get("properties", {}).items():
        flatten(spec, child, f"{path}.{name}", name in required_names, seen, out)
    if "items" in schema:
        flatten(spec, schema["items"], f"{path}[]", False, seen, out)