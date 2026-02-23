import sqlite3
import time
import streamlit as st
from google import genai

# ── 1. API CLIENT ───────────────────────────────────────────────
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ── 2. PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI Healthcare Assistant",
    page_icon="🩺",
    layout="centered"
)

# ── 3. DATABASE ─────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("healthcare.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, specialty TEXT,
            hospital TEXT, location TEXT, contact TEXT
        )
    """)
    c.execute("SELECT COUNT(*) FROM doctors")
    if c.fetchone()[0] == 0:
        doctors = [
            ("Dr. Priya Sharma",  "General Physician", "Apollo Clinic",       "Bangalore", "080-12345678"),
            ("Dr. Rajan Mehta",   "Cardiologist",      "Fortis Hospital",     "Bangalore", "080-87654321"),
            ("Dr. Anita Rao",     "Neurologist",       "Manipal Hospital",    "Bangalore", "080-11223344"),
            ("Dr. Suresh Kumar",  "Dermatologist",     "Columbia Asia",       "Bangalore", "080-55667788"),
            ("Dr. Meena Iyer",    "Nutritionist",      "Narayana Health",     "Bangalore", "080-99887766"),
            ("Dr. Arvind Nair",   "Orthopedic",        "Sakra World",         "Bangalore", "080-33445566"),
            ("Dr. Kavitha Reddy", "Gynecologist",      "Cloudnine Hospital",  "Bangalore", "080-77889900"),
            ("Dr. Sanjay Patel",  "Psychiatrist",      "NIMHANS",             "Bangalore", "080-22334455"),
            ("Dr. Lakshmi Das",   "Pediatrician",      "Indira Gandhi CH",    "Bangalore", "080-66778899"),
            ("Dr. Mohan Raj",     "Ophthalmologist",   "Narayana Nethralaya", "Bangalore", "080-44556677"),
        ]
        c.executemany(
            "INSERT INTO doctors (name, specialty, hospital, location, contact) VALUES (?,?,?,?,?)",
            doctors
        )
    conn.commit()
    conn.close()

def get_doctors():
    conn = sqlite3.connect("healthcare.db")
    c = conn.cursor()
    c.execute("SELECT name, specialty, hospital, location, contact FROM doctors")
    rows = c.fetchall()
    conn.close()
    return "\n".join([f"- {r[0]} ({r[1]}) at {r[2]}, {r[3]}. Contact: {r[4]}" for r in rows])

init_db()

# ── 4. SYSTEM PROMPT ────────────────────────────────────────────
SYSTEM_PROMPT = """You are a warm, helpful, and responsible AI Healthcare Assistant named HealthBot.

You have four core capabilities:
1. SYMPTOM CHECKER - Describe possible causes for symptoms. Never diagnose definitively.
2. DIET & NUTRITION - Provide personalized diet plans based on health goals or conditions.
3. MEDICINE INFO - Give general info about medicines: uses, side effects. Never prescribe.
4. FIND LOCAL DOCTORS - Use the directory in context to recommend suitable specialists.

RULES:
- Always be empathetic and friendly.
- Always end with a disclaimer to consult a real doctor.
- Never give a definitive diagnosis or prescribe dosages.
- If someone describes an emergency (chest pain, difficulty breathing), immediately tell them to call 112.
- Keep responses clear and well structured. Use bullet points where helpful."""

# ── 5. SESSION STATE ────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []

# ── 6. SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.title("🩺 HealthBot")
    st.markdown("Your AI-powered health companion.")
    st.divider()
    st.markdown("### What I can do")
    st.markdown("""
- 🩻 **Symptom Checker**
- 🥗 **Diet & Nutrition Plans**
- 💊 **Medicine Information**
- 🏥 **Find Local Doctors**
    """)
    st.divider()
    st.markdown("### Quick Questions")
    quick_questions = [
        "I have a headache and fever",
        "Suggest a diet for diabetes",
        "What is Paracetamol used for?",
        "Find a cardiologist near me",
        "I have chest pain",
        "Suggest a weight loss diet",
    ]
    for q in quick_questions:
        if st.button(q, use_container_width=True):
            st.session_state.pending_prompt = q
    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()
    st.caption("⚠️ For informational purposes only. Always consult a qualified doctor.")

# ── 7. MAIN UI ──────────────────────────────────────────────────
st.markdown("## 🩺 AI Healthcare Assistant")
st.caption("Ask me about symptoms, diet plans, medicines, or finding a doctor.")

# Welcome message
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown("""
👋 **Hello! I'm HealthBot, your AI healthcare companion.**

I can help you with:
- 🩻 Checking your symptoms
- 🥗 Creating personalized diet plans
- 💊 Providing medicine information
- 🏥 Finding local doctors in Bangalore

**How are you feeling today? Tell me your symptoms or ask me anything!**

> ⚠️ *I'm an AI assistant, not a medical professional. Always consult a real doctor for diagnosis and treatment.*
        """)

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── 8. SEND MESSAGE FUNCTION ────────────────────────────────────
def send_message(prompt):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Add doctor context if needed
    contextual_prompt = prompt
    doctor_keywords = ["doctor", "specialist", "find", "hospital", "clinic",
                       "neurologist", "cardiologist", "dermatologist",
                       "gynecologist", "pediatrician", "psychiatrist",
                       "orthopedic", "ophthalmologist", "nutritionist"]
    if any(word in prompt.lower() for word in doctor_keywords):
        contextual_prompt += f"\n\n[Local doctor directory:\n{get_doctors()}]"

    # Build full conversation with history for context
    full_prompt = SYSTEM_PROMPT + "\n\n"
    for msg in st.session_state.history:
        role = "User" if msg["role"] == "user" else "HealthBot"
        full_prompt += f"{role}: {msg['content']}\n"
    full_prompt += f"User: {contextual_prompt}\nHealthBot:"

    # Get AI response with retry
    response = None
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            for attempt in range(3):
                try:
                    result = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=full_prompt
                    )
                    response = result.text
                    st.markdown(response)
                    break
                except Exception as e:
                    err = str(e)
                    if "ResourceExhausted" in err or "429" in err:
                        if attempt < 2:
                            wait = (attempt + 1) * 10
                            st.warning(f"⏳ High demand, retrying in {wait}s...")
                            time.sleep(wait)
                        else:
                            st.error("⚠️ Service busy. Please wait a minute and try again.")
                    elif "API_KEY_INVALID" in err or "API key not valid" in err:
                        st.error("⚠️ Invalid API key. Please check your Streamlit Secrets.")
                        break
                    elif "NotFound" in err:
                        st.error("⚠️ Model not available. Try updating your API key.")
                        break
                    else:
                        st.error(f"⚠️ Error: {err}")
                        break

    if response:
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.history.append({"role": "user", "content": prompt})
        st.session_state.history.append({"role": "assistant", "content": response})

# ── 9. HANDLE INPUT ─────────────────────────────────────────────
if "pending_prompt" in st.session_state:
    prompt = st.session_state.pop("pending_prompt")
    send_message(prompt)

if prompt := st.chat_input("Describe your symptoms, ask about medicines, diet plans, or find a doctor..."):
    send_message(prompt)
