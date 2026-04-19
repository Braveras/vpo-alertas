import json
import logging
from pathlib import Path
from typing import Set, List
from models import Listing

logger = logging.getLogger(__name__)

DEFAULT_SEEN_FILE = Path(__file__).parent / "seen.json"


def load_seen(path: Path = DEFAULT_SEEN_FILE) -> Set[str]:
    if not path.exists():
        return set()
    try:
        with open(path) as f:
            return set(json.load(f))
    except (json.JSONDecodeError, ValueError):
        logger.warning(f"Corrupted seen.json at {path}, starting fresh")
        return set()


def save_seen(seen: Set[str], path: Path = DEFAULT_SEEN_FILE) -> None:
    with open(path, "w") as f:
        json.dump(sorted(seen), f, indent=2)


def filter_new(listings: List[Listing], seen: Set[str]) -> List[Listing]:
    return [l for l in listings if l.id not in seen]
