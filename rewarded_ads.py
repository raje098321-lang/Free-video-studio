"""Rewarded-ad integration boundary.

Do not grant credits from a browser button alone. In production, configure a
supported rewarded-ad provider and validate its server-side completion signal.
This starter intentionally does not fake an ad view or reward.
"""
import os
from fastapi import HTTPException

ADS_MODE=os.getenv("REWARDED_ADS_MODE","disabled").lower()

def reward_provider_status():
    return {
        "mode":ADS_MODE,
        "ready":False,
        "message":"Rewarded ads require publisher/ad-unit setup and server-side completion verification."
    }

def verify_completion(payload:dict):
    # TODO: Implement the exact verification flow for your ad network:
    # signature/SSV validation, nonce or transaction ID, user binding,
    # timestamp, and replay protection. Never trust a client-only callback.
    raise HTTPException(501,"Rewarded ad provider is not configured. Credits are not granted in this starter.")
