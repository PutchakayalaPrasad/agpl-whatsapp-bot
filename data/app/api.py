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
# ==================================================
def load_team_players(text):
    teams = {}
    current_team = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("[") and line.endswith("]"):
            current_team = line[1:-1]
            teams[current_team] = []
        elif current_team:
            teams[current_team].append(line)

    return teams

TEAM_PLAYERS = load_team_players(TEAMS_TEXT)

# ==================================================
# MESSAGE PROCESSOR
# ==================================================
def process_user_message(msg):
    msg = msg.lower().strip()

    # ---------- GREETINGS ----------
    if msg in ["hi", "hello", "hey", "good morning", "good evening"]:
        return (
            "Hello 👋\n\n"
            "Welcome to AGPL–2026 WhatsApp Assistant 🏏\n\n"
            "You can ask:\n"
            "• About AGPL\n"
            "• Tournament format\n"
            "• Points system\n"
            "• Day 2 matches\n"
            "• East team players\n"
            "• Player name"
        )

    # ---------- ABOUT ----------
    if "about" in msg:
        return extract_section(ABOUT_TEXT, "ABOUT")

    if "purpose" in msg:
        return extract_section(ABOUT_TEXT, "PURPOSE")

    if "format" in msg or "rules" in msg:
        return extract_section(ABOUT_TEXT, "FORMAT")

    if "date" in msg:
        return extract_section(ABOUT_TEXT, "DATES")

    if "points" in msg:
        return extract_section(ABOUT_TEXT, "POINTS")

    if "teams" in msg:
        return extract_section(ABOUT_TEXT, "TEAMS")

    # ---------- DAY MATCHES (SMART FIX ✅) ----------
    day_match = re.search(r"day\s*[-]?\s*(\d)", msg)
    if day_match:
        day_number = day_match.group(1)
        section_name = f"DAY_{day_number}"
        result = extract_section(SCHEDULE_TEXT, section_name)
        if result:
            return result

    # ---------- OTHER SCHEDULE ----------
    if "final" in msg:
        return extract_section(SCHEDULE_TEXT, "FINAL")

    if "timing" in msg:
        return extract_section(SCHEDULE_TEXT, "TIMINGS")

    if "bowling" in msg and "15" in msg:
        return extract_section(SCHEDULE_TEXT, "BOWLING_15_OVERS")

    if "bowling" in msg and "20" in msg:
        return extract_section(SCHEDULE_TEXT, "BOWLING_20_OVERS")

    # ---------- ALL PLAYERS ----------
    if "all players" in msg or "players list" in msg:
        output = ["🏏 AGPL Team Players\n"]
        for team, players in TEAM_PLAYERS.items():
            output.append(f"{team} Team:")
            for p in players:
                output.append(f"• {p}")
            output.append("")
        return "\n".join(output).strip()

    # ---------- PLAYER SEARCH ----------
    for team, players in TEAM_PLAYERS.items():
        for player in players:
            if player.lower() == msg:
                return f"🏏 Player Details\n\nName: {player}\nTeam: {team}"

    # ---------- TEAM PLAYERS ----------
    for team, players in TEAM_PLAYERS.items():
        if team.lower() in msg:
            return "\n".join(
                [f"🏏 {team} Team Players"] +
                [f"• {p}" for p in players]
            )

    # ---------- FALLBACK ----------
    return (
        "Sorry, I couldn’t understand your request ❌\n\n"
        "Try asking:\n"
        "• About AGPL\n"
        "• Day 2 matches\n"
        "• West team players\n"
        "• Player name"
    )

# ==================================================
# WHATSAPP WEBHOOK
# ==================================================
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    incoming_msg = form.get("Body", "")

    print("Incoming WhatsApp message:", incoming_msg)

    reply_text = process_user_message(incoming_msg)

    resp = MessagingResponse()
    resp.message(reply_text)

    return Response(
        content=str(resp),
        media_type="application/xml"
    )
