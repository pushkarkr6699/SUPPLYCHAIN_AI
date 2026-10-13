"""Hosted startup with optional private asset provisioning and fixed model validation."""
from pathlib import Path
import os
import sys
import tempfile
from urllib.parse import urlsplit
from urllib.request import urlopen
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    url = os.getenv('SUPPLYCHAIN_ASSET_BUNDLE_URL', '').strip()
    if url:
        from services.deployment_assets import install, MAX_BYTES
        pinned = os.getenv('SUPPLYCHAIN_ASSET_BUNDLE_SHA256', '').strip()
        if len(pinned) != 64 or any(c not in '0123456789abcdef' for c in pinned):
            raise ValueError('Configure a valid private deployment bundle checksum.')
        if urlsplit(url).scheme != 'https':
            raise ValueError('Private bundle downloads require HTTPS.')
        # Never print the URL: signed storage links may contain credentials.
        try:
            with urlopen(url, timeout=90) as response:
                if urlsplit(response.geturl()).scheme != 'https':
                    raise ValueError('Bundle redirects require HTTPS.')
                payload = response.read(MAX_BYTES+1)
            if len(payload) > MAX_BYTES:
                raise ValueError('Private asset bundle exceeds the size limit.')
        except Exception:
            raise RuntimeError('Private deployment bundle download failed; verify server-only storage configuration.') from None
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'assets.zip'
            archive.write_bytes(payload)
            install(archive, pinned)
        from services.inference_service import validate_registered_delivery_model
        from services.demand_inference import validate as validate_demand
        from services.profitability_inference import validate_conversion as validate_profit
        from services.final_delivery_inference import validate_conversion as validate_final
        for validate in (validate_registered_delivery_model, validate_demand, validate_profit, validate_final):
            result = validate()
            if result.get('status') != 'validated':
                raise RuntimeError('A registered model failed validation in the hosted runtime.')
        print('Private registered assets installed; four model adapters validated.', flush=True)
    port = os.getenv('PORT', '8501')
    if not port.isdigit() or not 1 <= int(port) <= 65535:
        raise ValueError('Invalid hosted port.')
    os.execv(sys.executable, [sys.executable, '-m', 'streamlit', 'run', str(ROOT/'app.py'),
                           '--server.address=0.0.0.0', '--server.port='+port])


if __name__ == '__main__':
    main()
