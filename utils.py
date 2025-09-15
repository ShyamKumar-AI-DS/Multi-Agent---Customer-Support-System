from typing import Dict, Any
import uuid
import json
from datetime import datetime

def now_iso():
    return datetime.utcnow().isoformat() + "Z"


def generate_id(prefix: str = "t"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# Simple in-memory ticket DB
TICKET_DB: Dict[str, Dict[str, Any]] = {}


# Simple log function
def log(info: str, **kwargs):
    entry = {"ts": now_iso(), "info": info, **kwargs}
    print(json.dumps(entry))