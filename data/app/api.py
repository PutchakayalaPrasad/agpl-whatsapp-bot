from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import requests
import os
import re

app = FastAPI(title="AGPL WhatsApp Bot (Meta Cloud API)")

# ==================================================
# CONFIGURATION
# ==================================================
VERIFY_TOKEN = "agpl_verify_token_2026"  # must match Meta dashboard

META_TOKEN = os.getenv("META_TOKEN")           # set in Render
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID") # set in Render

# ==================================================
# HEALTH CHECK
# ==================================================
@app.get("/")
def health():
    return {"status": "AGPL Meta WhatsApp Bot is running"}

# ==================================================
# WEBHOOK VERIFICATION (META REQUIRES THIS EXACTLY)
# ==================================================
@app.get("/webhook")
def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        # MUST return challenge as plain text
        return PlainTextResponse(content=challenge)

    return PlainTextResponse(content="Verification failed", status_code=403)

# ==================================================
# SEND MESSAGE USING META API
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

    requests.post(url, headers=headers, json=payload)

# ==================================================
# WEBHOOK RECEIVER (INCOMING MESSAGES)
# ==================================================
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = message["from"]           # user's phone number
        text = message["text"]["body"]     # message text
    except Exception:
        # Ignore non-message events
        return {"status": "ignored"}

    text_lower = text.lower()

    # ==================================================
    # BASIC TEST LOGIC (YOU CAN EXPAND LATER)
    # ==================================================
    if "hi" in text_lower or "hello" in text_lower:
        reply = (
            "Hello 👋\n\n"
            "Welcome to AGPL–2026 WhatsApp Bot 🏏\n\n"
            "You can ask:\n"
            "• About AGPL\n"
            "• Rules\n"
            "• Points\n"
            "• Day 2 matches"
        )
    elif "about" in text_lower:
        reply = "AGPL–2026 is a village-level tennis ball cricket tournament."
    elif "rule" in text_lower:
        reply = "AGPL format: League matches 15 overs, Final 20 overs."
    elif "point" in text_lower:
        reply = "Win: 2 points\nLoss: 0 points\nTie: 1 point"
    elif re.search(r"day\s*2", text_lower):
        reply = "Day 2 Matches:\n• West vs South – 7:45 AM\n• North vs Palem – 10:45 AM"
    else:
        reply = "Sorry, I didn’t understand. Try: about, rules, points, day 2."

    send_whatsapp_message(sender, reply)
    return {"status": "ok"}
