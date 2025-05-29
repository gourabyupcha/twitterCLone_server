import json
from typing import Dict, Any
from datetime import timedelta, datetime
import random

DB_PATH = "db.json"

def load_db() -> Dict[str, Any]:
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_db(data: Dict[str, Any]):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_random_timestamp():
    now = datetime.utcnow()
    delta = timedelta(days=random.randint(0,7), hours=random.randint(0,23), minutes=random.randint(0,59))
    random_time = now - delta
    return random_time.isoformat()
