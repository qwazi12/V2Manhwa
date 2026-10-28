"""Export implemented API only; the full blueprint OpenAPI remains a design."""
import json
from pathlib import Path
from flamingo_next_api.main import create_app
root = Path(__file__).resolve().parents[1]
(root / 'contracts/local.openapi.json').write_text(json.dumps(create_app().openapi(), indent=2) + '\n')
