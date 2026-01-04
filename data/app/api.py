from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from pathlib import Path
import re

app = FastAPI(title="AGPL WhatsApp Assistant")

# ==================================================
# PATHS & FILE LOADING
# ==================================================
BASE_DIR = Path(__file__).resolve().parent.parent

ABOUT_TEXT = (BASE_DIR / "about_agpl.txt").read_text(
    encoding="utf-8", errors="ignore"
)
SCHEDULE_TEXT = (BASE_DIR / "agpl_2026_schedule.txt").read_text(
    encoding="utf-8", errors="ignore"
)
TEAMS_TEXT = (BASE_DIR / "cricket_teams.txt").read_text(
    encoding="utf-8", errors="ignore"
)

# ==================================================
# BRACKET SECTION EXTRACTOR (ABOUT FILE)
# ==================================================
def extract_bracket_section(text, section):
    section = section.lower().strip()
    lines = text.splitlines()

    collecting = False
    result = []

    for line in lines:
        clean = line.strip().lower()

        if clean.startswith("[") and clean.endswith("]"):
            header = clean.strip("[]").strip()
            if header == section:
                collecting = True
                continue
            elif collecting:
                break

        if collecting:
            result.append(line)

    output = "\n".join(result).strip()
    return output if output else "No information available for this topic."

# ==================================================
# DAY SCHEDULE EXTRACTOR (SCHEDULE FILE)
# ==================================================
def extract_day_schedule(text, day_number):
    day_pattern = re.compile(rf"DAY\s+{day_number}\b", re.IGNORECASE)
    lines = text.splitlines()

    collecting = False
    result = []

    for line in lines:
        if day_pattern.search(line):
            collecting = True
            result.append(line)
            continue

        if collecting:
            if re.search(r"DAY\s+\d+\b", line, re.IGNORECASE):
                break
            result.append(line)

    output = "\n".join(result).strip()
    return output if output else "No schedule found for this day."

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
            current_team = line.strip("[]").strip()
            teams[current_team] = []
        elif current_team:
            teams[current_team].append(line)

    return teams

TEAM_PLAYERS = load_team_players(TEAMS_TEXT)

# ==================================================
# MESSAGE PROCESSOR
# ==================================================
def process_user_message(msg):
    msg = msg.lower()
    msg = re.sub(r"[^\w\s-]", "", msg)

    # ---------- GREETING ----------
    if msg in ["hi", "hello", "hey", "good morning", "good evening"]:
        return (
            "Hello 👋\n\n"
            "Welcome to AGPL–2026 WhatsApp Assistant 🏏\n\n"
            "You can ask:\n"
            "• About AGPL\n"
            "• Purpose\n"
            "• Rules / format\n"
            "• Points system\n"
            "• Day 2 matches\n"
            "• Team players\n"
            "• Player name"
        )

    # ---------- ABOUT FILE ----------
    if "about" in msg:
        return extract_bracket_section(ABOUT_TEXT, "about")

    if "purpose" in msg:
        return extract_bracket_section(ABOUT_TEXT, "purpose")

    if "rule" in msg or "format" in msg:
        return extract_bracket_section(ABOUT_TEXT, "format")

    if "point" in msg:
        return extract_bracket_section(ABOUT_TEXT, "points")

    if "date" in msg:
        return extract_bracket_section(ABOUT_TEXT, "dates")

    if "team" in msg and "player" not in msg:
        return extract_bracket_section(ABOUT_TEXT, "teams")

    # ---------- DAY MATCHES ----------
    day_match = re.search(r"day\s*[-]?\s*(\d)", msg)
    if day_match:
        return extract_day_schedule(SCHEDULE_TEXT, day_match.group(1))

    # ---------- PLAYERS ----------
    if "all players" in msg or "players list" in msg:
        output = ["🏏 AGPL Team Players\n"]
        for team, players in TEAM_PLAYERS.items():
            output.append(f"{team} Team:")
            for p in players:
                output.append(f"• {p}")
            output.append("")
        return "\n".join(output).strip()

    for team, players in TEAM_PLAYERS.items():
        if team.lower() in msg:
            return "\n".join(
                [f"🏏 {team} Team Players"]
                + [f"• {p}" for p in players]
            )

    return (
        "Sorry, I couldn’t understand your request ❌\n\n"
        "Try asking:\n"
        "• About AGPL\n"
        "• Purpose\n"
        "• Rules\n"
        "• Points\n"
        "• Day 2 matches"
    )

# ==================================================
# WHATSAPP WEBHOOK
# ==================================================
@app.post("/whatsapp")
@app.post("/whatsapp/")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    incoming_msg = form.get("Body", "")

    reply_text = process_user_message(incoming_msg)

    if not reply_text.strip():
        reply_text = "Sorry, something went wrong. Please try again."

    resp = MessagingResponse()
    resp.message(reply_text)

    return Response(
        content=str(resp),
        media_type="application/xml; charset=utf-8"
    )

# ==================================================
# HEALTH CHECK
# ==================================================
@app.get("/")
def health():
    return {"status": "AGPL WhatsApp Bot is running"}
