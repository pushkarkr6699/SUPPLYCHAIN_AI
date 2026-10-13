"""Create a private, hash-pinned deployment bundle without publishing it to Git."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.deployment_assets import package

if __name__ == '__main__':
    destination = ROOT / 'backups/deployment/supplychain-connected-assets.zip'
    result = package(destination)
    result['private_bundle'] = str(destination.relative_to(ROOT))
    (destination.parent / 'bundle_manifest.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
