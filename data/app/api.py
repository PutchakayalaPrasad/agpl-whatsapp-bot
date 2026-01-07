from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from pathlib import Path
import requests, json, re, os

app = FastAPI(title="AGPL WhatsApp Bot (Meta)")

# ==================================================
# ENV VARIABLES
# ==================================================
META_TOKEN = os.getenv("META_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# ==================================================
# LOAD DATA (SINGLE FILE)
# ==================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA = json.loads((BASE_DIR / "agpl_data.json").read_text(encoding="utf-8"))

# ==================================================
# SEND MESSAGE (META CLOUD API)
# ==================================================
def send_message(to: str, text: str):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    r = requests.post(url, headers=headers, json=payload)
    print("SEND:", r.status_code, r.text)

# ==================================================
# MESSAGE LOGIC
# ==================================================
def process_message(msg: str):
    msg = msg.lower().strip()

    if msg in ["hi", "hello", "hey"]:
        return (
            "Hello 👋\nAGPL–2026 WhatsApp Bot 🏏\n\n"
            "Ask:\n"
            "• About AGPL\n"
            "• Rules / Points\n"
            "• Day 2 matches\n"
            "• Player name\n"
            "• Team name"
        )

    if "about" in msg:
        return DATA["about"]["description"]

    if "purpose" in msg:
        return "Purpose:\n" + "\n".join(f"• {p}" for p in DATA["about"]["purpose"])

    if "rule" in msg or "format" in msg:
        f = DATA["about"]["format"]
        return f"Format: {f['type']}\nLeague: {f['league_overs']} overs\nFinal: {f['final_overs']} overs"

    if "point" in msg:
        p = DATA["about"]["points"]
        return f"Points:\nWin – {p['win']}\nLoss – {p['loss']}\nTie – {p['tie']}"

    day_match = re.search(r"day\s*(\d)", msg)
    if day_match:
        day = f"day{day_match.group(1)}"
        matches = DATA["schedule"].get(day)
        if matches:
            return "\n".join(f"Day {m['day']} – {m['match']} at {m['time']}" for m in matches)

    for team, players in DATA["teams"].items():
        for player in players:
            if player.lower() in msg:
                team_matches = []
                for d in DATA["schedule"].values():
                    if isinstance(d, list):
                        for m in d:
                            if team in m["match"]:
                                team_matches.append(
                                    f"Day {m['day']} – {m['match']} at {m['time']}"
                                )
                return (
                    f"Player: {player}\nTeam: {team}\n\nMatches:\n" +
                    "\n".join(team_matches)
                )

    for team, players in DATA["teams"].items():
        if team.lower() in msg:
            team_matches = []
            for d in DATA["schedule"].values():
                if isinstance(d, list):
                    for m in d:
                        if team in m["match"]:
                            team_matches.append(
                                f"Day {m['day']} – {m['match']} at {m['time']}"
                            )
            return (
                f"{team} Team\n\nPlayers:\n" +
                "\n".join(f"• {p}" for p in players) +
                "\n\nMatches:\n" + "\n".join(team_matches)
            )

    return "Sorry ❌ I didn’t understand. Try: Prasad, West team, Day 2 matches"

# ==================================================
# WEBHOOK VERIFICATION (GET)
# ==================================================
@app.get("/webhook")
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    return PlainTextResponse("Verification failed", status_code=403)

# ==================================================
# RECEIVE MESSAGE (POST)
# ==================================================
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("INCOMING:", data)

    try:
        value = data["entry"][0]["changes"][0]["value"]
        message = value["messages"][0]
        sender = message["from"]
        text = message["text"]["body"]
    except Exception:
        return {"status": "ignored"}

    reply = process_message(text)
    send_message(sender, reply)
    return {"status": "ok"}

# ==================================================
# HEALTH
# ==================================================
@app.get("/")
def health():
    return {"status": "AGPL Meta WhatsApp Bot running"}
