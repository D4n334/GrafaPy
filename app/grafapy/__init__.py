from pathlib import Path

from dotenv import load_dotenv

_here = Path(__file__).resolve()
for _parent in (_here.parent, *_here.parents):
    _candidate = _parent / ".env"
    if _candidate.exists():
        load_dotenv(_candidate)
        break
else:
    load_dotenv()

__version__ = "0.1.0"
