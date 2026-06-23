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
    Retrieve the data you want to display from Rhythia.
    If an official API exists, call it here.
    If not, you may need to reverse‑engineer the API from the Rhythia web app
    or the bot's internal endpoints.

    This placeholder returns some dummy data so you can test the flow.
    Replace it with a real API call or data source.
    """
    # -----------------------------------------------------------------
    # Example using a hypothetical Rhythia API:
    #   api_url = f"https://api.rhythia.bot/v1/users/{user_id}"
    #   headers = {"Authorization": f"Bearer {BOT_TOKEN}"}  # if needed
    #   resp = requests.get(api_url, headers=headers)
    #   if resp.status_code == 200:
    #       return resp.json()
    #   else:
    #       logging.error(f"API returned {resp.status_code}: {resp.text}")
    #       return None
    # -----------------------------------------------------------------

    # Placeholder dummy data - remove this when you integrate the real source.
    return {
        "level": 42,
        "score": 123456,
        "avatar_url": "https://cdn.discordapp.com/avatars/604624172613894144/avatar.png",
        "status": "vibing to lofi beats"
    }

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