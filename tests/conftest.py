import sys
import os
from pathlib import Path
os.environ.setdefault("SUPPLYCHAIN_PROVIDER", "demo")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

