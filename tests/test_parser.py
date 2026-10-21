from pathlib import Path

import pytest

from tethermap.contracts.models import FieldSpec
from tethermap.contracts.parser import load_contract

FIXTURE = Path(__file__).parent / "fixtures" / "orders_v1.yaml"


@pytest.fixture
def contract():
    return load_contract(FIXTURE)


def write_spec(tmp_path, text):
    path = tmp_path / "spec.yaml"
    path.write_text(text)
    return path


def test_operations_are_keyed_by_method_and_path(contract):
    assert set(contract.operations) == {"GET /orders", "POST /orders", "GET /orders/{id}"}


def test_query_parameter_with_enum(contract):
    request = contract.operations["GET /orders"].request
    assert request == {"query.status": FieldSpec("string", False, frozenset({"open", "closed"}))}


def test_path_level_parameter_applies_to_operation(contract):
    request = contract.operations["GET /orders/{id}"].request
    assert request == {"path.id": FieldSpec("integer", True)}


def test_request_body_fields_and_nullable_type(contract):
    request = contract.operations["POST /orders"].request
    assert request["body"] == FieldSpec("object", True)
    assert request["body.customer"] == FieldSpec("string", True)
    assert request["body.note"] == FieldSpec("string", False)


def test_all_of_and_array_items_in_response(contract):
    body = contract.operations["GET /orders"].responses["200"]
    assert body["body"] == FieldSpec("array", True)
    assert body["body[]"] == FieldSpec("object", False)
    assert body["body[].customer"] == FieldSpec("string", True)
    assert body["body[].id"] == FieldSpec("integer", True)
    assert body["body[].lines[].sku"] == FieldSpec("string", False)


def test_response_without_body_is_empty(contract):
    assert contract.operations["GET /orders/{id}"].responses["404"] == {}


def test_unsupported_version_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="Unsupported OpenAPI version"):
        load_contract(write_spec(tmp_path, "swagger: '2.0'\npaths: {}\n"))


def test_external_reference_is_rejected(tmp_path):
    spec = """
openapi: 3.0.3
paths:
  /a:
    get:
      responses:
        "200":
          description: ok
          content:
            application/json:
              schema:
                $ref: other.yaml#/Thing
"""
    with pytest.raises(ValueError, match="Only local references"):
        load_contract(write_spec(tmp_path, spec))


def test_recursive_schema_terminates(tmp_path):
    spec = """
openapi: 3.0.3
paths:
  /tree:
    get:
      responses:
        "200":
          description: ok
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Node"
components:
  schemas:
    Node:
      type: object
      properties:
        children:
          type: array
          items:
            $ref: "#/components/schemas/Node"
"""
    body = load_contract(write_spec(tmp_path, spec)).operations["GET /tree"].responses["200"]
    assert body["body.children[]"] == FieldSpec(None, False)