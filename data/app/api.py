from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from pathlib import Path
import json
import re

app = FastAPI(title="AGPL WhatsApp Bot")

# ==================================================
# LOAD SINGLE DATA FILE
# ==================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA = json.loads((BASE_DIR / "agpl_data.json").read_text(encoding="utf-8"))

# ==================================================
# MESSAGE LOGIC
# ==================================================
def process_message(msg: str):
    msg = msg.lower().strip()

    if msg in ["hi", "hello", "hey"]:
        return (
            "Hello 👋\n\n"
            "AGPL–2026 WhatsApp Bot 🏏\n\n"
            "Ask:\n"
            "• About AGPL\n"
            "• Purpose\n"
            "• Rules\n"
            "• Points\n"
            "• Day 2 matches\n"
            "• West team players"
        )

    if "about" in msg:
        return DATA["about"]["description"]

    if "purpose" in msg:
        return "Purpose:\n" + "\n".join(f"• {p}" for p in DATA["about"]["purpose"])

    if "rule" in msg or "format" in msg:
        f = DATA["about"]["format"]
        return (
            f"Format: {f['type']}\n"
            f"League: {f['league_overs']} overs\n"
            f"Final: {f['final_overs']} overs"
        )

    if "point" in msg:
        p = DATA["about"]["points"]
        return f"Points:\nWin – {p['win']}\nLoss – {p['loss']}\nTie – {p['tie']}"

    day_match = re.search(r"day\s*(\d)", msg)
    if day_match:
        day = f"day{day_match.group(1)}"
        matches = DATA["schedule"].get(day)
        if matches:
            return "\n".join(
                [f"🏏 {m['match']} at {m['time']}" for m in matches]
            )

    if "final" in msg:
        return DATA["schedule"]["final"]

    for team, players in DATA["teams"].items():
        if team.lower() in msg:
            return "\n".join(
                [f"🏏 {team} Team Players"] +
                [f"• {p}" for p in players]
            )

    return (
        "Sorry ❌ I didn’t understand.\n\n"
        "Try:\n"
        "• About AGPL\n"
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

    reply = process_message(incoming_msg)

    resp = MessagingResponse()
    resp.message(reply)

    return PlainTextResponse(str(resp), media_type="application/xml")

@app.get("/")
def health():
    return {"status": "AGPL WhatsApp Bot running"}
