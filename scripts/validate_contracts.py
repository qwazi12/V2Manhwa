#!/usr/bin/env python3
import json
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
spec=yaml.safe_load((ROOT/"contracts/openapi.yaml").read_text())
contract=json.loads((ROOT/"contracts/ai_contracts.schema.json").read_text())
wf=yaml.safe_load((ROOT/"contracts/workflows.yaml").read_text())
Draft202012Validator.check_schema(contract)
assert len(spec["paths"])==48
assert len(contract["$defs"])==22
assert len(wf["stages"])==25
print("Reference contracts validated: 48 paths / 22 AI definitions / 25 stages")
print("Contract validation is static; production API endpoints are NOT implemented.")
