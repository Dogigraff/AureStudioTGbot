import time
from typing import Dict

# user_id -> timestamp
last_lead_time: Dict[int, float] = {}

def can_submit_lead(user_id: int, min_interval_sec: int = 60) -> bool:
    now = time.time()
    last = last_lead_time.get(user_id, 0)
    return (now - last) >= min_interval_sec

def update_lead_time(user_id: int):
    last_lead_time[user_id] = time.time()
