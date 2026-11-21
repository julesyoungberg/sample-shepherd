"""app/src/lib/events.ts hand-copies events.schema.json; a field it gets wrong is a type the app gets wrong."""
import json
import re
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "src" / "sample_shepherd" / "events.schema.json").read_text(encoding="utf-8"))
TS = (ROOT / "app" / "src" / "lib" / "events.ts").read_text(encoding="utf-8")
FIXTURES = sorted((ROOT / "app" / "src" / "lib" / "fixtures").glob("*.jsonl"))


def ts_fields(marker):
    """{field: type text} of the TS type whose body contains `marker`, e.g. "Event<'warn'>" or "kind: 'issue'"."""
    for body in TS.split("export type ")[1:]:
        if marker in body:
            return dict(re.findall(r"(\w+)\??:\s*([^;\n}]+)", body))
    raise AssertionError(f"no type in events.ts has {marker}")


def schema_types():
    """(name, TS marker, schema properties, required fields) for each event type and row kind."""
    for event in SCHEMA["oneOf"]:
        kind = event["properties"]["type"]["const"]
        if kind == "row":
            for rule in event["allOf"]:
                row = rule["if"]["properties"]["kind"]["const"]
                yield f"row kind {row!r}", f"kind: '{row}'", rule["then"]["properties"], rule["then"]["required"]
        else:
            yield f"event {kind!r}", f"Event<'{kind}'>", event["properties"], event["required"]


@pytest.mark.parametrize("name, marker, props, required", list(schema_types()), ids=lambda v: v if isinstance(v, str) else "")
def test_events_ts_matches_the_schema(name, marker, props, required):
    ts = ts_fields(marker)
    missing = set(required) - set(ts)
    assert not missing, f"events.ts {name} lacks {missing}"
    for field, spec in props.items():
        if "const" in spec:
            continue
        if "enum" in spec:
            assert set(re.findall(r"'([^']+)'", ts[field])) == set(spec["enum"]), f"events.ts {name}.{field} values"
        nullable = "null" in spec.get("type", [])
        assert nullable == ("null" in ts[field]), f"events.ts {name}.{field}: schema nullable is {nullable}"


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda p: p.name)
def test_recorded_fixtures_match_the_schema(fixture):
    for line in fixture.read_text(encoding="utf-8").splitlines():
        if line.strip():
            jsonschema.validate(json.loads(line), SCHEMA)
