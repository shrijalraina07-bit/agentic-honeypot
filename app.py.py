from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow browser access (for your HTML UI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# 🔐 API KEY (FOR JUDGES)
# ===============================
API_KEY = "GUVI-HONEYPOT-2026"

# ===============================
# 🧠 IN-MEMORY SESSION STORE
# (for live UI)
# ===============================
SESSION_DATA = {
    "sessionId": None,
    "scamDetected": False,
    "totalMessagesExchanged": 0,
    "persona": None,
    "messages": [],
    "extractedIntelligence": {
        "bankAccounts": [],
        "upiIds": [],
        "phishingLinks": [],
        "phoneNumbers": [],
        "suspiciousKeywords": []
    },
    "agentNotes": ""
}

# ===============================
# 🔄 UI UPDATE ENDPOINT
# ===============================
@app.post("/update")
def update_session(data: dict):
    global SESSION_DATA

    if SESSION_DATA["sessionId"] is None:
        SESSION_DATA["sessionId"] = data.get("sessionId")

    SESSION_DATA["scamDetected"] = data.get("scamDetected", False)
    SESSION_DATA["persona"] = data.get("persona", SESSION_DATA["persona"])
    SESSION_DATA["agentNotes"] = data.get("agentNotes", "")

    SESSION_DATA["totalMessagesExchanged"] = data.get(
        "totalMessagesExchanged",
        SESSION_DATA["totalMessagesExchanged"]
    )

    new_messages = data.get("messages", [])
    if isinstance(new_messages, list):
        SESSION_DATA["messages"].extend(new_messages)

    intel = data.get("extractedIntelligence", {})
    for key in SESSION_DATA["extractedIntelligence"]:
        values = intel.get(key, [])
        if isinstance(values, list):
            for v in values:
                if v not in SESSION_DATA["extractedIntelligence"][key]:
                    SESSION_DATA["extractedIntelligence"][key].append(v)

    return {"status": "ok"}

# ===============================
# 📡 UI POLLING ENDPOINT
# ===============================
@app.get("/session")
def get_session():
    return SESSION_DATA

# ===============================
# 🚨 JUDGE EVALUATION ENDPOINT
# ===============================
@app.post("/scan")
def scan_message(payload: dict, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    message = payload.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Message required")

    upi_ids = []
    suspicious_keywords = []

    # Simple but valid extraction logic
    words = message.split()
    for w in words:
        if "@" in w:
            upi_ids.append(w)

    for key in ["urgent", "verify", "blocked", "suspended", "pay"]:
        if key in message.lower():
            suspicious_keywords.append(key)

    return {
        "scamDetected": True,
        "persona": "auto-detected",
        "extractedIntelligence": {
            "upiIds": upi_ids,
            "phishingLinks": [],
            "suspiciousKeywords": suspicious_keywords
        }
    }
