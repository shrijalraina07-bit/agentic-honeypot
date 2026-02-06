import requests
import re
from scam_detector import is_scam_message

API_URL = "http://localhost:8000/update"
SESSION_ID = "wertyu-dfghj-ertyui"

# -----------------------------
# PERSONA DEFINITIONS
# -----------------------------

PERSONA_RULES = {
    "senior": {
        "style": """
You are an elderly, confused, anxious person.
You fear losing money.
You type slowly, emotionally, sometimes rambling.
No abbreviations.
""",
        "escalation_speed": "slow"
    },
    "student": {
        "style": """
You are a young student.
You are impatient and want quick resolution.
You use casual language.
You get frustrated easily.
""",
        "escalation_speed": "medium"
    },
    "business": {
        "style": """
You are a business owner.
You are under time pressure.
You want exact steps immediately.
You are assertive and transactional.
""",
        "escalation_speed": "fast"
    }
}

# -----------------------------
# PERSONA DETECTION
# -----------------------------

def detect_persona_from_message(message):
    msg = message.lower()

    if any(k in msg for k in ["invoice", "gst", "business", "tax"]):
        return "business"
    if any(k in msg for k in ["job", "internship", "salary", "placement"]):
        return "student"
    if any(k in msg for k in ["police", "court", "account blocked"]):
        return "senior"

    return "senior"

# -----------------------------
# ESCALATION STAGE
# -----------------------------

def get_escalation_stage(turns, speed):
    if speed == "slow":
        return "early" if turns < 4 else "middle" if turns < 9 else "late"
    if speed == "medium":
        return "early" if turns < 3 else "middle" if turns < 7 else "late"
    return "early" if turns < 2 else "middle" if turns < 5 else "late"

# -----------------------------
# ESCALATION RULES
# -----------------------------

ESCALATION_RULES = {
    "early": "You are confused and asking for clarification.",
    "middle": "You are worried and asking for exact steps.",
    "late": "You are stressed and demand precise payment details."
}

# -----------------------------
# PROMPT BUILDER
# -----------------------------

def build_prompt(persona, conversation_history, turns):
    stage = get_escalation_stage(turns, PERSONA_RULES[persona]["escalation_speed"])

    history = ""
    for sender, msg in conversation_history[-6:]:
        history += f"{sender}: {msg}\n"

    return f"""
SYSTEM:
You are a real human. Never mention AI.

PERSONA:
{PERSONA_RULES[persona]["style"]}

ESCALATION:
{ESCALATION_RULES[stage]}

CONVERSATION:
{history}

Respond with ONE message.
""".strip()

# -----------------------------
# OLLAMA CALL
# -----------------------------

def generate_reply(prompt):
    res = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "llama3", "prompt": prompt, "stream": False},
        timeout=60
    )
    return res.json()["response"].strip()

# -----------------------------
# DETECT BANK DATA
# -----------------------------

def contains_upi(msg):
    return re.search(r"\b[\w.-]+@[a-zA-Z]+\b", msg) is not None

# -----------------------------
# MAIN LOOP
# -----------------------------

def run_test_chat():
    conversation_history = []
    turns = 0

    scammer_msg = input("Scammer: ")
    persona = detect_persona_from_message(scammer_msg)

    conversation_history.append(("Scammer", scammer_msg))

    while True:
        prompt = build_prompt(persona, conversation_history, turns)
        reply = generate_reply(prompt)

        print(f"\nHuman: {reply}\n")

        conversation_history.append(("Agent", reply))
        turns += 1

        # ✅ SEND ONLY NEW MESSAGES
        payload = {
            "sessionId": SESSION_ID,
            "scamDetected": contains_upi(scammer_msg),
            "persona": persona,
            "totalMessagesExchanged": turns,
            "messages": [
                {"sender": "Scammer", "text": scammer_msg},
                {"sender": "Agent", "text": reply}
            ],
            "extractedIntelligence": {
                "upiIds": re.findall(r"\b[\w.-]+@[a-zA-Z]+\b", scammer_msg)
            },
            "agentNotes": "Live honeypot interaction"
        }

        requests.post(API_URL, json=payload, timeout=5)

        if contains_upi(scammer_msg):
            print("\n[Conversation terminated — banking details detected]\n")
            break

        scammer_msg = input("Scammer: ")
        conversation_history.append(("Scammer", scammer_msg))

# -----------------------------
# RUN
# -----------------------------

if __name__ == "__main__":
    run_test_chat()
