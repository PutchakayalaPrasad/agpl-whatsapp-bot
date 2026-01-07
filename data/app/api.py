from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from pathlib import Path
import re

app = FastAPI(title="AGPL WhatsApp Bot (Twilio)")

# ==================================================
# LOAD DATA FILES
# ==================================================
BASE_DIR = Path(__file__).resolve().parent.parent

ABOUT_TEXT = (BASE_DIR / "about_agpl.txt").read_text(encoding="utf-8")
SCHEDULE_TEXT = (BASE_DIR / "agpl_2026_schedule.txt").read_text(encoding="utf-8")
TEAMS_TEXT = (BASE_DIR / "cricket_teams.txt").read_text(encoding="utf-8")

# ==================================================
# TEAM → PLAYER PARSER
# ==================================================
def load_team_players(text):
    teams = {}
    current_team = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current_team = line.strip("[]")
            teams[current_team] = []
        elif current_team:
            teams[current_team].append(line)

    return teams

TEAM_PLAYERS = load_team_players(TEAMS_TEXT)

# ==================================================
# FLEXIBLE SECTION EXTRACTOR (FIXED)
# ==================================================
def extract_between(text, start_keywords, stop_keywords):
    collecting = False
    result = []

    for line in text.splitlines():
        lower = line.lower()

        if any(k in lower for k in start_keywords):
            collecting = True
            continue

        if collecting and any(k in lower for k in stop_keywords):
            break

        if collecting:
            result.append(line)

    return "\n".join(result).strip()

# ==================================================
# MESSAGE LOGIC
# ==================================================
def process_message(msg: str):
    msg = msg.lower().strip()

    if msg in ["hi", "hello", "hey"]:
        return (
            "Hello 👋\n\n"
            "Welcome to AGPL–2026 WhatsApp Bot 🏏\n\n"
            "Ask me:\n"
            "• About AGPL\n"
            "• Rules / Format\n"
            "• Points system\n"
            "• Day 2 matches\n"
            "• Team players"
        )

    # ABOUT FILE
    if "about" in msg:
        return extract_between(ABOUT_TEXT, ["about"], ["purpose"])

    if "purpose" in msg:
        return extract_between(ABOUT_TEXT, ["purpose"], ["format"])

    if "rule" in msg or "format" in msg:
        return extract_between(ABOUT_TEXT, ["format"], ["dates"])

    if "point" in msg:
        return extract_between(ABOUT_TEXT, ["points"], [""])

    if "date" in msg:
        return extract_between(ABOUT_TEXT, ["dates"], ["teams"])

    if "teams" in msg:
        return extract_between(ABOUT_TEXT, ["teams"], ["points"])

    # DAY MATCHES (WORKS WITH YOUR FILE)
    day_match = re.search(r"day\s*-?\s*(\d)", msg)
    if day_match:
        day = day_match.group(1)
        return extract_between(
            SCHEDULE_TEXT,
            [f"day {day}"],
            [f"day {int(day)+1}", "final"]
        )

    # TEAM PLAYERS
    for team, players in TEAM_PLAYERS.items():
        if team.lower() in msg:
            return "\n".join(
                [f"🏏 {team} Team Players"] +
                [f"• {p}" for p in players]
            )

    return (
        "Sorry ❌ I didn’t understand.\n\n"
        "Try:\n"
        "• About AGPL\n"
        "• Rules\n"
        "• Day 2 matches\n"
        "• West team players"
    )

# ==================================================
# TWILIO WEBHOOK
# ==================================================
@app.post("/whatsapp")
@app.post("/whatsapp/")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    incoming_msg = form.get("Body", "")

    print("Incoming WhatsApp message:", incoming_msg)

    reply_text = process_message(incoming_msg)

    resp = MessagingResponse()
    resp.message(reply_text)

    return PlainTextResponse(
        content=str(resp),
        media_type="application/xml"
    )

# ==================================================
# HEALTH CHECK
# ==================================================
@app.get("/")
def health():
    return {"status": "AGPL Twilio WhatsApp Bot running"}
