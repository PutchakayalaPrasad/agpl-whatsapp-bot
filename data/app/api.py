from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import requests
import os
import re

app = FastAPI(title="AGPL WhatsApp Bot - Meta Cloud API")

# ==================================================
# CONFIGURATION (ENV VARIABLES)
# ==================================================
VERIFY_TOKEN = "agpl_verify_token_2026"

META_TOKEN = os.getenv("META_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# ==================================================
# BASIC VALIDATION (LOG AT STARTUP)
# ==================================================
print("META_TOKEN loaded:", "YES" if META_TOKEN else "NO")
print("PHONE_NUMBER_ID:", PHONE_NUMBER_ID)

# ==================================================
# HEALTH CHECK
# ==================================================
@app.get("/")
def health():
    return {"status": "AGPL Meta WhatsApp Bot is running"}

# ==================================================
# WEBHOOK VERIFICATION (META → GET)
# ==================================================
@app.get("/webhook")
def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    print("VERIFY REQUEST:", mode, token, challenge)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge)

    return PlainTextResponse(content="Verification failed", status_code=403)

# ==================================================
# SEND MESSAGE TO WHATSAPP (META API)
# ==================================================
def send_whatsapp_message(to: str, text: str):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": text
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    # 🔴 IMPORTANT DEBUG LOGS
    print("SEND TO:", to)
    print("SEND STATUS:", response.status_code)
    print("SEND RESPONSE:", response.text)

# ==================================================
# RECEIVE MESSAGE FROM WHATSAPP (META → POST)
# ==================================================
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()

    print("INCOMING PAYLOAD:", data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = message["from"]
        text = message["text"]["body"]
    except Exception as e:
        print("NON-MESSAGE EVENT OR ERROR:", e)
        return {"status": "ignored"}

    text_lower = text.lower().strip()
    print("INCOMING MESSAGE FROM:", sender, "| TEXT:", text_lower)

    # ==================================================
    # SIMPLE LOGIC (FOR TESTING)
    # ==================================================
    if text_lower in ["hi", "hello", "hlo"]:
        reply = (
            "Hello 👋\n\n"
            "Welcome to AGPL–2026 WhatsApp Bot 🏏\n\n"
            "Try:\n"
            "• about\n"
            "• rules\n"
            "• points\n"
            "• day 2"
        )

    elif "about" in text_lower:
        reply = "AGPL–2026 is a village-level tennis ball cricket tournament."

    elif "rule" in text_lower or "format" in text_lower:
        reply = "League matches: 15 overs\nFinal match: 20 overs"

    elif "point" in text_lower:
        reply = "Win: 2 points\nLoss: 0 points\nTie: 1 point"

    elif re.search(r"day\s*2", text_lower):
        reply = (
            "Day 2 Matches:\n"
            "• West vs South – 7:45 AM\n"
            "• North vs Palem – 10:45 AM\n"
            "• East vs South – 2:45 PM"
        )

    else:
        reply = "Sorry, I didn’t understand. Try: about, rules, points, day 2."

    send_whatsapp_message(sender, reply)
    return {"status": "ok"}
