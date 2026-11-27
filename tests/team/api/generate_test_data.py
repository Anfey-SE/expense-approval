"""
Automated EP & 3-Point BVA Test Data Generator from OpenAPI 3.0 Spec.

Reads an OpenAPI YAML file (default: tests/team/api/openapi.yaml) and produces
Equivalence Partitioning (EP) classes and 3-point Boundary Value Analysis (BVA)
test vectors in JSON format (default: tests/team/api/generated_test_data.json).

Usage:
    python tests/team/api/generate_test_data.py
    python tests/team/api/generate_test_data.py --spec path/to/openapi.yaml --out path/to/out.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

import yaml


def resolve_ref(spec: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    """Resolve a local $ref pointer inside the OpenAPI document."""
    if "$ref" not in node:
        return node
    ref = node["$ref"]
    if not ref.startswith("#/"):
        raise ValueError(f"Unsupported external $ref: {ref}")
    cur: Any = spec
    for part in ref[2:].split("/"):
        cur = cur[part]
    return cur


def make_string(length: int, char: str = "a") -> str:
    """Return a deterministic string of the requested length."""
    if length <= 0:
        return ""
    return char * length


def bva_for_string(name: str, prop: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate 3-point BVA cases for string length constraints."""
    cases: list[dict[str, Any]] = []
    min_len = prop.get("minLength")
    max_len = prop.get("maxLength")
    nullable = prop.get("nullable", False)

    if min_len is not None:
        if min_len > 0:
            cases.append({
                "field": name,
                "point": "below_min",
                "boundary": f"minLength={min_len}",
                "value": make_string(min_len - 1),
                "valid": False,
                "reason": f"Length {min_len - 1} < minLength {min_len}",
            })
        cases.append({
            "field": name,
            "point": "at_min",
            "boundary": f"minLength={min_len}",
            "value": make_string(min_len),
            "valid": True,
            "reason": f"Length {min_len} == minLength {min_len}",
        })
        if max_len is None or min_len + 1 <= max_len:
            cases.append({
                "field": name,
                "point": "above_min",
                "boundary": f"minLength={min_len}",
                "value": make_string(min_len + 1),
                "valid": True,
                "reason": f"Length {min_len + 1} > minLength {min_len}",
            })

    if max_len is not None:
        if min_len is None or max_len - 1 >= min_len:
            cases.append({
                "field": name,
                "point": "below_max",
                "boundary": f"maxLength={max_len}",
                "value": make_string(max_len - 1),
                "valid": True,
                "reason": f"Length {max_len - 1} < maxLength {max_len}",
            })
        cases.append({
            "field": name,
            "point": "at_max",
            "boundary": f"maxLength={max_len}",
            "value": make_string(max_len),
            "valid": True,
            "reason": f"Length {max_len} == maxLength {max_len}",
        })
        cases.append({
            "field": name,
            "point": "above_max",
            "boundary": f"maxLength={max_len}",
            "value": make_string(max_len + 1),
            "valid": False,
            "reason": f"Length {max_len + 1} > maxLength {max_len}",
        })

    if nullable:
        cases.append({
            "field": name,
            "point": "nullable",
            "boundary": "nullable=true",
            "value": None,
            "valid": True,
            "reason": "Optional nullable field omitted/null",
        })
    return cases


def bva_for_number(name: str, prop: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate 3-point BVA cases for numeric/integer constraints."""
    cases: list[dict[str, Any]] = []
    is_int = prop.get("type") == "integer"
    step = 1 if is_int else float(prop.get("multipleOf", 0.01))
    minimum = prop.get("minimum")
    maximum = prop.get("maximum")

    def fmt(val: float | int) -> float | int:
        return int(val) if is_int else round(float(val), 4)

    if minimum is not None:
        cases.extend([
            {
                "field": name,
                "point": "below_min",
                "boundary": f"minimum={minimum}",
                "value": fmt(minimum - step),
                "valid": False,
                "reason": f"Value {fmt(minimum - step)} < minimum {minimum}",
            },
            {
                "field": name,
                "point": "at_min",
                "boundary": f"minimum={minimum}",
                "value": fmt(minimum),
                "valid": True,
                "reason": f"Value {fmt(minimum)} == minimum {minimum}",
            },
            {
                "field": name,
                "point": "above_min",
                "boundary": f"minimum={minimum}",
                "value": fmt(minimum + step),
                "valid": True,
                "reason": f"Value {fmt(minimum + step)} > minimum {minimum}",
            },
        ])

    if maximum is not None:
        cases.extend([
            {
                "field": name,
                "point": "below_max",
                "boundary": f"maximum={maximum}",
                "value": fmt(maximum - step),
                "valid": True,
                "reason": f"Value {fmt(maximum - step)} < maximum {maximum}",
            },
            {
                "field": name,
                "point": "at_max",
                "boundary": f"maximum={maximum}",
                "value": fmt(maximum),
                "valid": True,
                "reason": f"Value {fmt(maximum)} == maximum {maximum}",
            },
            {
                "field": name,
                "point": "above_max",
                "boundary": f"maximum={maximum}",
                "value": fmt(maximum + step),
                "valid": False,
                "reason": f"Value {fmt(maximum + step)} > maximum {maximum}",
            },
        ])

    if not is_int and prop.get("multipleOf") == 0.01:
        cases.append({
            "field": name,
            "point": "invalid_precision",
            "boundary": "multipleOf=0.01",
            "value": 10.123,
            "valid": False,
            "reason": "3 decimal places exceeds 2-decimal precision",
        })
    return cases


def bva_for_array(name: str, prop: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate 3-point BVA cases for array minItems/maxItems."""
    cases: list[dict[str, Any]] = []
    min_items = prop.get("minItems")
    max_items = prop.get("maxItems")

    if min_items is not None:
        if min_items > 0:
            cases.append({
                "field": name,
                "point": "below_min",
                "boundary": f"minItems={min_items}",
                "count": min_items - 1,
                "valid": False,
                "reason": f"Item count {min_items - 1} < minItems {min_items}",
            })
        cases.append({
            "field": name,
            "point": "at_min",
            "boundary": f"minItems={min_items}",
            "count": min_items,
            "valid": True,
            "reason": f"Item count {min_items} == minItems {min_items}",
        })
        cases.append({
            "field": name,
            "point": "above_min",
            "boundary": f"minItems={min_items}",
            "count": min_items + 1,
            "valid": True,
            "reason": f"Item count {min_items + 1} > minItems {min_items}",
        })

    if max_items is not None:
        cases.extend([
            {
                "field": name,
                "point": "below_max",
                "boundary": f"maxItems={max_items}",
                "count": max_items - 1,
                "valid": True,
                "reason": f"Item count {max_items - 1} < maxItems {max_items}",
            },
            {
                "field": name,
                "point": "at_max",
                "boundary": f"maxItems={max_items}",
                "count": max_items,
                "valid": True,
                "reason": f"Item count {max_items} == maxItems {max_items}",
            },
            {
                "field": name,
                "point": "above_max",
                "boundary": f"maxItems={max_items}",
                "count": max_items + 1,
                "valid": False,
                "reason": f"Item count {max_items + 1} > maxItems {max_items}",
            },
        ])
    return cases


def bva_for_date(name: str, prop: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate 3-point BVA cases for date constraints."""
    today = dt.date.today()
    yesterday = today - dt.timedelta(days=1)
    tomorrow = today + dt.timedelta(days=1)
    if prop.get("x-constraint") == "pastOrPresent":
        return [
            {
                "field": name,
                "point": "below_max",
                "boundary": "pastOrPresent=today",
                "value": yesterday.isoformat(),
                "valid": True,
                "reason": "Yesterday is in the past",
            },
            {
                "field": name,
                "point": "at_max",
                "boundary": "pastOrPresent=today",
                "value": today.isoformat(),
                "valid": True,
                "reason": "Today is at the PastOrPresent boundary",
            },
            {
                "field": name,
                "point": "above_max",
                "boundary": "pastOrPresent=today",
                "value": tomorrow.isoformat(),
                "valid": False,
                "reason": "Tomorrow is in the future (violates PastOrPresent)",
            },
        ]
    return []


def ep_for_property(name: str, prop: dict[str, Any], required: bool) -> list[dict[str, Any]]:
    """Generate Equivalence Partitioning classes for a property."""
    partitions: list[dict[str, Any]] = []
    ptype = prop.get("type", "string")
    fmt = prop.get("format")

    if "enum" in prop:
        for val in prop["enum"]:
            partitions.append({"field": name, "class": f"valid_enum_{val}", "value": val, "valid": True})
        partitions.append({"field": name, "class": "invalid_enum", "value": "INVALID_ENUM_VALUE", "valid": False})
        return partitions

    if ptype == "string":
        if fmt == "email":
            partitions.extend([
                {"field": name, "class": "valid_email", "value": "valid.user@acme.com", "valid": True},
                {"field": name, "class": "invalid_email_no_at", "value": "not-an-email", "valid": False},
                {"field": name, "class": "invalid_blank", "value": "   ", "valid": False},
            ])
        elif fmt == "date":
            today = dt.date.today()
            partitions.extend([
                {"field": name, "class": "valid_past_date", "value": (today - dt.timedelta(days=7)).isoformat(), "valid": True},
                {"field": name, "class": "invalid_future_date", "value": (today + dt.timedelta(days=30)).isoformat(), "valid": False},
                {"field": name, "class": "invalid_date_format", "value": "2026-99-99", "valid": False},
            ])
        else:
            min_len = prop.get("minLength", 0)
            max_len = prop.get("maxLength", 50)
            mid_len = max(min_len, min(10, max_len))
            if name == "currency":
                partitions.extend([
                    {"field": name, "class": "valid_iso_currency_upper", "value": "EUR", "valid": True},
                    {"field": name, "class": "valid_iso_currency_lower", "value": "gbp", "valid": True},
                    {"field": name, "class": "valid_null_defaults_usd", "value": None, "valid": True},
                    {"field": name, "class": "invalid_too_short", "value": "US", "valid": False},
                    {"field": name, "class": "invalid_too_long", "value": "USDD", "valid": False},
                ])
            else:
                partitions.append({
                    "field": name,
                    "class": "valid_typical_string",
                    "value": make_string(mid_len, "x"),
                    "valid": True,
                })
                if min_len >= 1:
                    partitions.append({"field": name, "class": "invalid_empty_string", "value": "", "valid": False})
                    partitions.append({"field": name, "class": "invalid_whitespace_only", "value": "   ", "valid": False})
                if max_len is not None:
                    partitions.append({
                        "field": name,
                        "class": "invalid_exceeds_maxLength",
                        "value": make_string(max_len + 5, "z"),
                        "valid": False,
                    })
    elif ptype in ("number", "integer"):
        minimum = prop.get("minimum", 0)
        maximum = prop.get("maximum", 1000)
        mid = int((minimum + min(maximum, 100)) / 2) if ptype == "integer" else round((minimum + min(maximum, 100.0)) / 2, 2)
        partitions.extend([
            {"field": name, "class": "valid_mid_range", "value": mid, "valid": True},
            {"field": name, "class": "invalid_negative", "value": -5 if ptype == "integer" else -1.00, "valid": False},
        ])
        if minimum > 0:
            partitions.append({"field": name, "class": "invalid_zero", "value": 0, "valid": False})

    if required:
        partitions.append({"field": name, "class": "invalid_missing_null", "value": None, "valid": False})

    return partitions


def generate(spec_path: Path) -> dict[str, Any]:
    """Parse OpenAPI spec and return structured EP + BVA test data."""
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    schemas = spec.get("components", {}).get("schemas", {})

    constraints_snapshot: dict[str, Any] = {}
    ep_cases: dict[str, list[dict[str, Any]]] = {}
    bva_cases: dict[str, list[dict[str, Any]]] = {}

    for schema_name, schema in schemas.items():
        if schema.get("type") != "object":
            continue
        required_fields = set(schema.get("required", []))
        props = schema.get("properties", {})
        ep_list: list[dict[str, Any]] = []
        bva_list: list[dict[str, Any]] = []
        schema_constraints: dict[str, Any] = {}

        for prop_name, raw_prop in props.items():
            prop = resolve_ref(spec, raw_prop)
            ptype = prop.get("type")
            schema_constraints[prop_name] = {
                k: prop[k]
                for k in ("type", "minLength", "maxLength", "minimum", "maximum", "multipleOf", "minItems", "maxItems", "nullable", "x-constraint")
                if k in prop
            }
            ep_list.extend(ep_for_property(prop_name, prop, prop_name in required_fields))
            if ptype == "string":
                if prop.get("format") == "date":
                    bva_list.extend(bva_for_date(prop_name, prop))
                else:
                    bva_list.extend(bva_for_string(prop_name, prop))
            elif ptype in ("number", "integer"):
                bva_list.extend(bva_for_number(prop_name, prop))
            elif ptype == "array":
                bva_list.extend(bva_for_array(prop_name, prop))

        constraints_snapshot[schema_name] = schema_constraints
        ep_cases[schema_name] = ep_list
        bva_cases[schema_name] = bva_list

    # Also extract query/path parameters from paths
    param_ep: list[dict[str, Any]] = []
    param_bva: list[dict[str, Any]] = []
    for path_key, path_item in spec.get("paths", {}).items():
        for method, op in path_item.items():
            if not isinstance(op, dict) or method == "parameters":
                continue
            for param in op.get("parameters", []):
                pname = f"{method.upper()} {path_key} [{param['in']}:{param['name']}]"
                pschema = resolve_ref(spec, param.get("schema", {}))
                param_ep.extend(ep_for_property(pname, pschema, param.get("required", False)))
                if pschema.get("type") in ("integer", "number"):
                    param_bva.extend(bva_for_number(pname, pschema))

    ep_cases["Parameters"] = param_ep
    bva_cases["Parameters"] = param_bva

    total_ep = sum(len(v) for v in ep_cases.values())
    total_bva = sum(len(v) for v in bva_cases.values())

    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "spec_title": spec.get("info", {}).get("title"),
        "spec_version": spec.get("info", {}).get("version"),
        "summary": {
            "total_ep_cases": total_ep,
            "total_bva_cases": total_bva,
            "total_cases": total_ep + total_bva,
        },
        "constraints_snapshot": constraints_snapshot,
        "ep_cases": ep_cases,
        "bva_cases": bva_cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate EP & 3-point BVA test data from OpenAPI spec.")
    default_dir = Path(__file__).resolve().parent
    parser.add_argument("--spec", type=Path, default=default_dir / "openapi.yaml")
    parser.add_argument("--out", type=Path, default=default_dir / "generated_test_data.json")
    args = parser.parse_args()

    data = generate(args.spec)
    args.out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Generated {data['summary']['total_ep_cases']} EP cases and {data['summary']['total_bva_cases']} BVA cases -> {args.out}")


if __name__ == "__main__":
    main()
