#!/usr/bin/env python3
"""
Update the Discord profile widget for the Rhythia application.
Reads configuration from environment variables:
  BOT_TOKEN        - Discord Bot token for the Rhythia app
  USER_ID          - Your Discord user ID (default: 604624172613894144)
  APPLICATION_ID   - Rhythia's application ID (default: 1516952439474098176)
"""

import os
import sys
import requests
import logging
from typing import Any, Dict, List, Optional

# ------------------------------------------------------------
# Configuration (from environment)
# ------------------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("BOT_TOKEN environment variable not set")
    sys.exit(1)

USER_ID = os.environ.get("USER_ID", "604624172613894144")
APPLICATION_ID = os.environ.get("APPLICATION_ID", "1516952439474098176")

DISCORD_API_URL = (
    f"https://discord.com/api/v9/applications/{APPLICATION_ID}"
    f"/users/{USER_ID}/identities/0/profile"
)

# ------------------------------------------------------------
# Data types for the widget (as per the TypeScript enums)
# ------------------------------------------------------------
DATA_TYPE_STRING = 1
DATA_TYPE_NUMBER = 2
DATA_TYPE_MEDIA  = 3

def build_dynamic_data(stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert raw stats from Rhythia into the 'dynamic' array expected by Discord.
    Modify this function based on the actual fields you want to display and
    the structure of the data returned by Rhythia's API.
    """
    dynamic: List[Dict[str, Any]] = []

    # Example: assume stats contains 'level', 'score', 'avatar', 'status'
    if "level" in stats:
        dynamic.append({
            "type": DATA_TYPE_NUMBER,
            "name": "Level",
            "value": stats["level"]
        })
    if "score" in stats:
        dynamic.append({
            "type": DATA_TYPE_NUMBER,
            "name": "Score",
            "value": stats["score"]
        })
    if "avatar_url" in stats:
        dynamic.append({
            "type": DATA_TYPE_MEDIA,
            "name": "Avatar",
            "value": {"url": stats["avatar_url"]}
        })
    if "status" in stats:
        dynamic.append({
            "type": DATA_TYPE_STRING,
            "name": "Status",
            "value": stats["status"]
        })

    # Add more fields as needed.
    # The 'name' should be a short display label, the 'value' must match the type.
    return dynamic

# ------------------------------------------------------------
# Data fetching – YOU MUST IMPLEMENT THIS
# ------------------------------------------------------------
def fetch_rhythia_data(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch user data from the Rhythia backend.
    Tries production.rhythia.com first, then falls back to Supabase.
    """
    # Option 1: Try the production.rhythia.com API
    api_url = f"https://production.rhythia.com/api/users/{user_id}/stats"
    headers = {
        "Authorization": f"Bearer {BOT_TOKEN}",  # if the API expects a Bearer token
        "Content-Type": "application/json"
    }
    try:
        resp = requests.get(api_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # Map fields according to the actual response structure
            return {
                "level": data.get("level"),
                "score": data.get("score"),
                "avatar_url": data.get("avatar_url"),
                "status": data.get("status")
            }
        else:
            logging.warning(f"Primary API returned {resp.status_code}, trying Supabase...")
    except requests.RequestException as e:
        logging.warning(f"Primary API request failed: {e}, trying Supabase...")

    # Option 2: Direct Supabase access (requires an anon/public key)
    supabase_url = "https://pfkajngbllcbdzoylrvp.supabase.co/rest/v1"
    # Assume there is a table named "users" or "profiles" – adjust accordingly
    table = "profiles"  # change this to the actual table name
    endpoint = f"{supabase_url}/{table}?user_id=eq.{user_id}&select=*"
    headers = {
        "apikey": os.environ.get("SUPABASE_ANON_KEY", ""),
        "Authorization": f"Bearer {os.environ.get('SUPABASE_ANON_KEY', '')}"
    }
    try:
        resp = requests.get(endpoint, headers=headers, timeout=10)
        if resp.status_code == 200:
            rows = resp.json()
            if rows:
                row = rows[0]
                return {
                    "level": row.get("level"),
                    "score": row.get("score"),
                    "avatar_url": row.get("avatar_url"),
                    "status": row.get("status")
                }
        else:
            logging.error(f"Supabase API returned {resp.status_code}: {resp.text}")
    except requests.RequestException as e:
        logging.error(f"Supabase request failed: {e}")

    # If all attempts fail, return None
    return None

# ------------------------------------------------------------
# Main update logic
# ------------------------------------------------------------
def update_widget() -> None:
    # 1. Fetch data from Rhythia
    stats = fetch_rhythia_data(USER_ID)
    if stats is None:
        logging.error("Failed to retrieve Rhythia data, widget not updated.")
        sys.exit(1)

    # 2. Build the payload
    dynamic_items = build_dynamic_data(stats)
    payload = {
        "data": {
            "dynamic": dynamic_items
        }
    }

    # 3. Send PATCH request to Discord
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bot {BOT_TOKEN}"
    }

    try:
        resp = requests.patch(DISCORD_API_URL, json=payload, headers=headers)
        if resp.status_code == 200 or resp.status_code == 204:
            logging.info("Widget updated successfully.")
        else:
            logging.error(
                f"Discord API error {resp.status_code}: {resp.text}"
            )
            sys.exit(1)
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    update_widget()