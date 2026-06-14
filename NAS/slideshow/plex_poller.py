#!/usr/local/bin/python3.14
"""
Polls the local Plex Media Server for active sessions and writes
a plex-status.json file that the slideshow reads every 30 seconds.

Setup:
  1. Fill in PLEX_TOKEN and PLEX_USER below.
  2. Copy this file to /volume1/photo/slideshow/plex_poller.py on the NAS.
  3. In DSM → Task Scheduler → Create → Scheduled Task → User-defined script:
       - Schedule: every 1 minute
       - Run command: /usr/local/bin/python3.14 /volume1/photo/slideshow/plex_poller.py
  4. Install any Python 3.x via Web Station → Script Language Settings (3.12+ recommended).

Finding your Plex token:
  Sign in to plex.tv → open any media item → click "···" → Get Info →
  View XML → look for X-Plex-Token= in the URL.
"""

import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

# ── Configure these ───────────────────────────────────────────────────────────
PLEX_TOKEN  = "YOUR_PLEX_TOKEN"         # your Plex auth token
PLEX_USER   = "YOUR_PLEX_USERAME"       # account name to watch (case-sensitive)
PLEX_HOST   = "IP_OF_PLEX_SERVER"       # Plex server (separate from NAS)
PLEX_PORT   = 32400
OUTPUT_FILE = "/volume1/<webroot>/slideshow/plex-status.json"
# ─────────────────────────────────────────────────────────────────────────────


def thumb_url(path):
    """Build a full Plex thumbnail URL from a /library/metadata/... path."""
    if not path:
        return ""
    return f"http://{PLEX_HOST}:{PLEX_PORT}{path}?X-Plex-Token={PLEX_TOKEN}"


def fetch_sessions():
    url = f"http://{PLEX_HOST}:{PLEX_PORT}/status/sessions?X-Plex-Token={PLEX_TOKEN}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.read().decode("utf-8")
    except Exception:
        return None


def parse_status(xml_text):
    """Return a dict with now-playing info for PLEX_USER, or {} if nothing."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return {}

    for item in root:
        user_el = item.find(".//User")
        if user_el is None:
            continue
        if user_el.get("title", "").lower() != PLEX_USER.lower():
            continue

        media_type = item.get("type", "")
        title      = item.get("title", "")

        if media_type == "track":
            # parentThumb = album art; grandparentThumb = artist art
            thumb = item.get("parentThumb", "") or item.get("thumb", "")
            return {
                "type":   "track",
                "title":  title,
                "artist": item.get("grandparentTitle", ""),
                "album":  item.get("parentTitle", ""),
                "thumb":  thumb_url(thumb),
            }
        elif media_type == "episode":
            # grandparentThumb = show poster (more recognizable than episode screenshot)
            thumb = item.get("grandparentThumb", "") or item.get("thumb", "")
            return {
                "type":   "episode",
                "title":  title,
                "show":   item.get("grandparentTitle", ""),
                "season": item.get("parentTitle", ""),
                "thumb":  thumb_url(thumb),
            }
        elif media_type == "movie":
            return {
                "type":  "movie",
                "title": title,
                "year":  item.get("year", ""),
                "thumb": thumb_url(item.get("thumb", "")),
            }
        else:
            return {
                "type":  media_type,
                "title": title,
                "thumb": thumb_url(item.get("thumb", "")),
            }

    return {}


def write_status(data):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def main():
    xml = fetch_sessions()
    if xml is None:
        write_status({})
        return

    status = parse_status(xml)
    write_status(status)


if __name__ == "__main__":
    main()
