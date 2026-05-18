from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bot import get_bot_response

# ============================================================
# APP SETUP
# ============================================================

app = FastAPI(title="Ecommerce Chatbot API")

# CORS — permet au frontend (React) de parler au backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en production mets ton domaine
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# MODELS
# ============================================================

class MessageRequest(BaseModel):
    message: str

class MessageResponse(BaseModel):
    reply: str

# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def root():
    return {"status": "Bot is running 🚀"}


@app.post("/chat", response_model=MessageResponse)
def chat(request: MessageRequest):
    reply = get_bot_response(request.message)
    return MessageResponse(reply=reply)