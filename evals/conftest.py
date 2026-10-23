import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
# Keep pytest off the real ~/.paperclip. A shell PAPERCLIP_HOME still wins.
os.environ.setdefault("PAPERCLIP_HOME", str(_REPO / ".paperclip-test"))
sys.path.insert(0, str(_REPO))
