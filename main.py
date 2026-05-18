from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx

from bot import get_bot_response

# ============================================================
# CONFIG — بدّل هاد القيم بعد ما تاخذهم من Facebook
# ============================================================

PAGE_ACCESS_TOKEN = "YOUR_PAGE_ACCESS_TOKEN"   # من Facebook Developer
VERIFY_TOKEN      = "riwa9token123"             # أنت تختاره

# ============================================================
# APP SETUP
# ============================================================

app = FastAPI(title="Riwa9 Chatbot — Facebook Messenger")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# WEBHOOK VERIFICATION — Facebook يتحقق من الـ URL
# ============================================================

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)

    mode      = params.get("hub.mode")
    token     = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified!")
        return int(challenge)
    else:
        print("❌ Verification failed")
        return {"error": "Forbidden"}

# ============================================================
# RECEIVE MESSAGES — Facebook يبعت Messages هنا
# ============================================================

@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):

                sender_id = event["sender"]["id"]

                # تحقق واش هو message
                if "message" in event:
                    user_message = event["message"].get("text", "")

                    if user_message:
                        # جيب الجواب من bot.py
                        reply = get_bot_response(user_message)

                        # بعث الجواب لـ Facebook
                        await send_message(sender_id, reply)

    return {"status": "ok"}

# ============================================================
# SEND MESSAGE — يبعت الجواب لـ Messenger
# ============================================================

async def send_message(recipient_id: str, message_text: str):
    url = "https://graph.facebook.com/v19.0/me/messages"

    payload = {
        "recipient": {"id": recipient_id},
        "message":   {"text": message_text},
    }

    params = {"access_token": PAGE_ACCESS_TOKEN}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, params=params)
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
        else:
            print(f"✅ Message sent to {recipient_id}")

# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {"status": "Riwa9 Chatbot is running 🚀"}