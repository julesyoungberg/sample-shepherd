"""app/src/lib/events.ts hand-copies events.schema.json; a field missing there is a type the app gets wrong."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "src" / "sample_shepherd" / "events.schema.json").read_text(encoding="utf-8"))
TS = (ROOT / "app" / "src" / "lib" / "events.ts").read_text(encoding="utf-8")


def ts_fields(marker):
    """Field names of the TS type whose body contains `marker`, e.g. "Event<'warn'>" or "kind: 'issue'"."""
    for body in TS.split("export type ")[1:]:
        if marker in body:
            return set(re.findall(r"(\w+)\??:", body))
    raise AssertionError(f"no type in events.ts has {marker}")


def test_every_event_and_row_kind_has_its_required_fields():
    for event in SCHEMA["oneOf"]:
        kind = event["properties"]["type"]["const"]
        if kind == "row":
            for rule in event["allOf"]:
                row = rule["if"]["properties"]["kind"]["const"]
                missing = set(rule["then"]["required"]) - ts_fields(f"kind: '{row}'")
                assert not missing, f"events.ts row kind {row!r} lacks {missing}"
        else:
            missing = set(event["required"]) - ts_fields(f"Event<'{kind}'>")
            assert not missing, f"events.ts event {kind!r} lacks {missing}"
