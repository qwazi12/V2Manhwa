import json
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]

def test_specs_parse_and_have_expected_shapes():
    o=yaml.safe_load((ROOT/"contracts/openapi.yaml").read_text())
    assert o["openapi"].startswith("3.1")
    assert len(o["paths"])==48
    assert len([v for p in o["paths"].values() for k,v in p.items() if k.lower() in {"get","post","patch","put","delete"}])==52
    sch=json.loads((ROOT/"contracts/ai_contracts.schema.json").read_text())
    Draft202012Validator.check_schema(sch)
    assert len(sch["$defs"])==22
    flow=yaml.safe_load((ROOT/"contracts/workflows.yaml").read_text())
    assert len(flow["stages"])==25
    assert len(set(flow["stages"]))==25
    for k,v in flow["stages"].items():
        for d in v.get("dependencies",[]): assert d in flow["stages"],(k,d)

def test_implemented_openapi_matches_checked_in_contract():
    from flamingo_next_api.main import create_app
    assert json.loads((ROOT / 'contracts/local.openapi.json').read_text()) == create_app().openapi()
