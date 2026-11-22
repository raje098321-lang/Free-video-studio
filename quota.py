"""Credit/quota scaffold for ad-supported video generation.

Production must use a persistent database, authenticated user identity, and
server-side ad completion verification. This in-memory version is for local
testing only and resets when the process restarts.
"""
import os, time, threading
from collections import defaultdict

# One credit represents one short scene request. Configure scene length to match
# the provider/model you actually connect (default 5 seconds).
SCENE_SECONDS = int(os.getenv("SCENE_SECONDS_PER_CREDIT", "5"))
DAILY_FREE_CREDITS = int(os.getenv("DAILY_FREE_CREDITS", "1"))
REWARDED_CREDITS_PER_COMPLETION = int(os.getenv("REWARDED_CREDITS", "1"))
MAX_REWARDED_COMPLETIONS_PER_DAY = int(os.getenv("MAX_REWARDED_COMPLETIONS_PER_DAY", "5"))

_lock=threading.Lock()
_wallet=defaultdict(int)
_free_used=defaultdict(int)
_ad_count=defaultdict(int)
_day=defaultdict(lambda: int(time.time()//86400))

def _rollover(user):
    today=int(time.time()//86400)
    if _day[user] != today:
        _day[user]=today
        _free_used[user]=0
        _ad_count[user]=0

def status(user="demo-user"):
    with _lock:
        _rollover(user)
        return {
            "credits":_wallet[user],
            "free_credits_remaining":max(0,DAILY_FREE_CREDITS-_free_used[user]),
            "rewarded_ads_completed_today":_ad_count[user],
            "rewarded_ads_remaining_today":max(0,MAX_REWARDED_COMPLETIONS_PER_DAY-_ad_count[user]),
            "seconds_per_credit":SCENE_SECONDS,
            "max_project_seconds":240,
            "note":"Credits are app usage units, not a promise that a provider has free GPU capacity."
        }

def grant_verified_reward(user, completion_id):
    """Call only after ad-network server-side verification.
    completion_id must be unique and persisted in production to prevent replay.
    """
    if not completion_id:
        raise ValueError("Missing verified ad completion ID")
    with _lock:
        _rollover(user)
        if _ad_count[user] >= MAX_REWARDED_COMPLETIONS_PER_DAY:
            raise ValueError("Daily rewarded-ad limit reached")
        # Local demo idempotency only. Replace with DB unique constraint.
        key=(user,completion_id)
        if key in _seen:
            return status(user)
        _seen.add(key)
        _wallet[user]+=REWARDED_CREDITS_PER_COMPLETION
        _ad_count[user]+=1
        return status(user)

_seen=set()

def consume_credit(user="demo-user"):
    with _lock:
        _rollover(user)
        if _wallet[user] > 0:
            _wallet[user]-=1
            return "rewarded_credit"
        if _free_used[user] < DAILY_FREE_CREDITS:
            _free_used[user]+=1
            return "daily_free_credit"
        raise ValueError("No credits left. Watch an optional rewarded ad or try again after quota reset.")
