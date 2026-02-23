import sqlite3
import time
import streamlit as st
import google.generativeai as genai

# ── 1. PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI Healthcare Assistant",
    page_icon="🩺",
    layout="centered"
)

# ── 2. API KEY ──────────────────────────────────────────────────
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ── 3. DATABASE SETUP ───────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("healthcare.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            specialty TEXT,
            hospital TEXT,
            location TEXT,
            contact TEXT
        )
    """)
    c.execute("SELECT COUNT(*) FROM doctors")
    if c.fetchone()[0] == 0:
        doctors = [
            ("Dr. Priya Sharma",   "General Physician", "Apollo Clinic",      "Bangalore", "080-12345678"),
            ("Dr. Rajan Mehta",    "Cardiologist",      "Fortis Hospital",    "Bangalore", "080-87654321"),
            ("Dr. Anita Rao",      "Neurologist",       "Manipal Hospital",   "Bangalore", "080-11223344"),
            ("Dr. Suresh Kumar",   "Dermatologist",     "Columbia Asia",      "Bangalore", "080-55667788"),
            ("Dr. Meena Iyer",     "Nutritionist",      "Narayana Health",    "Bangalore", "080-99887766"),
            ("Dr. Arvind Nair",    "Orthopedic",        "Sakra World",        "Bangalore", "080-33445566"),
            ("Dr. Kavitha Reddy",  "Gynecologist",      "Cloudnine Hospital", "Bangalore", "080-77889900"),
            ("Dr. Sanjay Patel",   "Psychiatrist",      "NIMHANS",            "Bangalore", "080-22334455"),
            ("Dr. Lakshmi Das",    "Pediatrician",      "Indira Gandhi CH",   "Bangalore", "080-66778899"),
            ("Dr. Mohan Raj",      "Ophthalmologist",   "Narayana Nethralaya","Bangalore", "080-44556677"),
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
    lines = []
    for r in rows:
        lines.append(f"- {r[0]} ({r[1]}) at {r[2]}, {r[3]}. Contact: {r[4]}")
    return "\n".join(lines)

init_db()

# ── 4. AI MODEL ─────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are a warm, helpful, and responsible AI Healthcare Assistant named "HealthBot".
You have four core capabilities:

1. SYMPTOM CHECKER — When users describe symptoms, ask clarifying questions if needed,
   then give a general overview of possible causes. Always remind them to see a doctor
   for proper diagnosis. Never diagnose definitively.

2. DIET & NUTRITION — Provide personalized diet plans and nutritional advice based on
   the user's health goals, conditions, or preferences (e.g. diabetic diet, weight loss,
   high protein, vegetarian etc.)

3. MEDICINE INFO — Give general information about common medicines: what they are used for,
   typical dosage ranges, common side effects. Never prescribe. Always say "consult your
   doctor or pharmacist before taking any medicine."

4. FIND LOCAL DOCTORS — When the user wants to find a doctor or specialist, use the
   directory provided in the context to recommend the most suitable one based on their
   symptoms or needs.

RULES YOU MUST ALWAYS FOLLOW:
- Always be empathetic and friendly.
- Always end medical advice with a disclaimer to consult a real doctor.
- Never give a definitive diagnosis.
- Never recommend specific prescription dosages.
- If someone describes an emergency (chest pain, difficulty breathing, stroke symptoms),
  immediately tell them to call emergency services (112 in India).
- Keep responses clear, structured, and easy to read. Use bullet points where helpful.
"""

@st.cache_resource
def load_model():
    return genai.GenerativeModel(
        model_name="gemini-pro",
        system_instruction=SYSTEM_PROMPT
    )

model = load_model()

# ── 5. SESSION STATE ────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# ── 6. SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/caduceus.png", width=60)
    st.title("HealthBot 🩺")
    st.markdown("Your AI-powered health companion.")
    st.divider()

    st.markdown("### What I can do")
    st.markdown("""
- 🩻 **Symptom Checker** — Describe how you feel
- 🥗 **Diet Plans** — Get personalized nutrition advice  
- 💊 **Medicine Info** — Learn about medications
- 🏥 **Find Doctors** — Locate specialists near you
    """)

    st.divider()

    st.markdown("### Quick Questions")
    quick = [
        "I have a headache and fever",
        "Suggest a diet for diabetes",
        "What is Paracetamol used for?",
        "Find a cardiologist near me",
        "I have chest pain",
        "Suggest a weight loss diet",
    ]
    for q in quick:
        if st.button(q, use_container_width=True):
            st.session_state.pending_prompt = q

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat = model.start_chat(history=[])
        st.rerun()

    st.caption("⚠️ This app is for informational purposes only. Always consult a qualified doctor for medical advice.")

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

# ── 8. HANDLE INPUT ─────────────────────────────────────────────
def send_message(prompt):
    # Show user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Build context-aware prompt
    contextual_prompt = prompt
    doctor_keywords = ["doctor", "specialist", "find", "hospital", "clinic", "neurologist",
                       "cardiologist", "dermatologist", "gynecologist", "pediatrician",
                       "psychiatrist", "orthopedic", "ophthalmologist", "nutritionist"]
    if any(word in prompt.lower() for word in doctor_keywords):
        doctor_data = get_doctors()
        contextual_prompt += f"\n\n[SYSTEM: Local doctor directory for recommendations:\n{doctor_data}]"

    # Get AI response
    response = None
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            for attempt in range(3):
                try:
                    response = st.session_state.chat.send_message(contextual_prompt)
                    st.markdown(response.text)
                    break
                except Exception as e:
                    err = str(e)
                    if "ResourceExhausted" in err or "429" in err:
                        if attempt < 2:
                            wait = (attempt + 1) * 10
                            st.warning(f"⏳ High demand, retrying in {wait}s...")
                            time.sleep(wait)
                        else:
                            st.error("⚠️ Service is busy right now. Please wait a minute and try again.")
                    elif "NotFound" in err:
                        st.error("⚠️ Model not available. Please check your API configuration.")
                        break
                    else:
                        st.error("⚠️ Something went wrong. Please try again.")
                        break

    if response:
        st.session_state.messages.append({"role": "assistant", "content": response.text})

# Handle sidebar quick question
if "pending_prompt" in st.session_state:
    prompt = st.session_state.pop("pending_prompt")
    send_message(prompt)

# Handle chat input
if prompt := st.chat_input("Describe your symptoms, ask about medicines, diet plans, or find a doctor..."):
    send_message(prompt)
