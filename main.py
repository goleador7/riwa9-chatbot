from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import httpx

from bot import get_bot_response

# ============================================================
# CONFIG
# ============================================================

PAGE_ACCESS_TOKEN = "YOUR_PAGE_ACCESS_TOKEN"
VERIFY_TOKEN      = "riwa9token123"

# ============================================================
# APP SETUP
# ============================================================

app = FastAPI(title="Riwa9 Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {"status": "Riwa9 Chatbot is running 🚀"}

# ============================================================
# WEBHOOK VERIFICATION
# ============================================================

@app.get("/webhook")
async def verify_webhook(request: Request):
    params    = dict(request.query_params)
    mode      = params.get("hub.mode")
    token     = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified!")
        return PlainTextResponse(content=challenge)

    print("❌ Verification failed")
    return PlainTextResponse(content="Forbidden", status_code=403)

# ============================================================
# RECEIVE MESSAGES
# ============================================================

@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]

                if "message" in event:
                    user_message = event["message"].get("text", "")
                    if user_message:
                        reply = get_bot_response(user_message)
                        await send_message(sender_id, reply)

    return {"status": "ok"}

# ============================================================
# SEND MESSAGE
# ============================================================

async def send_message(recipient_id: str, message_text: str):
    url     = "https://graph.facebook.com/v19.0/me/messages"
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
            print(f"✅ Sent to {recipient_id}")