from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from pathlib import Path
import re

app = FastAPI(title="AGPL WhatsApp Assistant")

# ==================================================
# PATHS & FILE LOADING
# ==================================================
BASE_DIR = Path(__file__).resolve().parent.parent

ABOUT_TEXT = (BASE_DIR / "about_agpl.txt").read_text(encoding="utf-8")
SCHEDULE_TEXT = (BASE_DIR / "agpl_2026_schedule.txt").read_text(encoding="utf-8")
TEAMS_TEXT = (BASE_DIR / "cricket_teams.txt").read_text(encoding="utf-8")

# ==================================================
# GENERIC SECTION EXTRACTOR
# ==================================================
def extract_section(text, section):
    lines = text.splitlines()
    result = []
    capture = False

    for line in lines:
        if line.strip() == f"[{section}]":
            capture = True
            continue
        if capture and line.startswith("[") and line.endswith("]"):
            break
        if capture:
            result.append(line)

    return "\n".join(result).strip()

# ==================================================
# TEAM → PLAYER PARSER
# ==================
