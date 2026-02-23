import sqlite3
import numpy as np
import streamlit as st
from groq import Groq
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ── 1. GROQ CLIENT ──────────────────────────────────────────────
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

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
            ("Dr. Priya Sharma",  "General Physician - treats fever, cold, flu, general illness, body pain, fatigue", "Apollo Clinic",       "Bangalore", "080-12345678"),
            ("Dr. Rajan Mehta",   "Cardiologist - treats chest pain, heart disease, blood pressure, palpitations",      "Fortis Hospital",     "Bangalore", "080-87654321"),
            ("Dr. Anita Rao",     "Neurologist - treats headache, migraine, dizziness, seizures, nerve pain",           "Manipal Hospital",    "Bangalore", "080-11223344"),
            ("Dr. Suresh Kumar",  "Dermatologist - treats skin rash, acne, eczema, hair loss, skin infections",         "Columbia Asia",       "Bangalore", "080-55667788"),
            ("Dr. Meena Iyer",    "Nutritionist - diet plans, weight loss, diabetes diet, obesity, nutrition advice",   "Narayana Health",     "Bangalore", "080-99887766"),
            ("Dr. Arvind Nair",   "Orthopedic - treats joint pain, back pain, bone fracture, arthritis, knee pain",     "Sakra World",         "Bangalore", "080-33445566"),
            ("Dr. Kavitha Reddy", "Gynecologist - treats women health, pregnancy, menstrual issues, PCOS",              "Cloudnine Hospital",  "Bangalore", "080-77889900"),
            ("Dr. Sanjay Patel",  "Psychiatrist - treats anxiety, depression, stress, mental health, insomnia",         "NIMHANS",             "Bangalore", "080-22334455"),
            ("Dr. Lakshmi Das",   "Pediatrician - treats children illness, child fever, kids health, infant care",      "Indira Gandhi CH",    "Bangalore", "080-66778899"),
            ("Dr. Mohan Raj",     "Ophthalmologist - treats eye pain, vision problems, eye infection, blurred vision",  "Narayana Nethralaya", "Bangalore", "080-44556677"),
        ]
        c.executemany(
            "INSERT INTO doctors (name, specialty, hospital, location, contact) VALUES (?,?,?,?,?)",
            doctors
        )
    conn.commit()
    conn.close()

def get_all_doctors():
    conn = sqlite3.connect("healthcare.db")
    c = conn.cursor()
    c.execute("SELECT name, specialty, hospital, location, contact FROM doctors")
    rows = c.fetchall()
    conn.close()
    return rows

init_db()

# ── 4. RAG — LOAD EMBEDDING MODEL ───────────────────────────────
@st.cache_resource
def load_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

@st.cache_resource
def build_doctor_embeddings():
    model = load_embedding_model()
    doctors = get_all_doctors()
    # Embed each doctor's specialty description
    specialty_texts = [doc[1] for doc in doctors]
    embeddings = model.encode(specialty_texts)
    return doctors, embeddings

def get_relevant_doctors(user_prompt, top_k=3):
    """RAG: Retrieve top_k most relevant doctors based on symptom similarity."""
    model = load_embedding_model()
    doctors, doctor_embeddings = build_doctor_embeddings()

    # Embed the user's prompt
    prompt_embedding = model.encode([user_prompt])

    # Calculate cosine similarity between prompt and all doctor specialties
    similarities = cosine_similarity(prompt_embedding, doctor_embeddings)[0]

    # Get top_k most similar doctors
    top_indices = np.argsort(similarities)[::-1][:top_k]

    # Only return doctors above a similarity threshold
    results = []
    for idx in top_indices:
        if similarities[idx] > 0.2:  # threshold to avoid irrelevant matches
            doc = doctors[idx]
            results.append(f"- {doc[0]} ({doc[1].split(' - ')[0]}) at {doc[2]}, {doc[3]}. Contact: {doc[4]}")

    return "\n".join(results) if results else ""

# ── 5. SYSTEM PROMPT ────────────────────────────────────────────
SYSTEM_PROMPT = """You are a warm, helpful, and responsible AI Healthcare Assistant named HealthBot.

You have four core capabilities:
1. SYMPTOM CHECKER - Describe possible causes for symptoms. Never diagnose definitively.
2. DIET & NUTRITION - Provide personalized diet plans based on health goals or conditions.
3. MEDICINE INFO - Give general info about medicines: uses, side effects. Never prescribe.
4. FIND LOCAL DOCTORS - When a doctor directory is provided in context, recommend the most suitable one based on the user's symptoms. Only recommend doctors when relevant.

RULES:
- Always be empathetic and friendly.
- Always end with a disclaimer to consult a real doctor.
- Never give a definitive diagnosis or prescribe dosages.
- If someone describes an emergency (chest pain, difficulty breathing), tell them to call 112 immediately.
- Keep responses clear and well structured. Use bullet points where helpful."""

# ── 6. SESSION STATE ────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── 7. SIDEBAR ──────────────────────────────────────────────────
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
        st.rerun()
    st.caption("⚠️ For informational purposes only. Always consult a qualified doctor.")

# ── 8. MAIN UI ──────────────────────────────────────────────────
st.markdown("## 🩺 AI Healthcare Assistant")
st.caption("Ask me about symptoms, diet plans, medicines, or finding a doctor.")

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

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── 9. SEND MESSAGE ─────────────────────────────────────────────
def send_message(prompt):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # ── RAG: Retrieve relevant doctors based on symptom similarity ──
    relevant_doctors = get_relevant_doctors(prompt)
    contextual_prompt = prompt
    if relevant_doctors:
        contextual_prompt += f"\n\n[Relevant doctors retrieved for these symptoms:\n{relevant_doctors}\nRecommend the most suitable one if appropriate.]"

    # Build messages for Groq with full conversation history
    groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in st.session_state.messages[:-1]:
        groq_messages.append({"role": msg["role"], "content": msg["content"]})
    groq_messages.append({"role": "user", "content": contextual_prompt})

    # Get response
    response = None
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=groq_messages,
                    max_tokens=1024,
                )
                response = result.choices[0].message.content
                st.markdown(response)
            except Exception as e:
                err = str(e)
                if "rate_limit" in err.lower() or "429" in err:
                    st.error("⚠️ Too many requests. Please wait a moment and try again.")
                elif "invalid_api_key" in err.lower() or "auth" in err.lower():
                    st.error("⚠️ Invalid API key. Please check your Streamlit Secrets.")
                else:
                    st.error(f"⚠️ Error: {err}")

    if response:
        st.session_state.messages.append({"role": "assistant", "content": response})

# ── 10. HANDLE INPUT ────────────────────────────────────────────
if "pending_prompt" in st.session_state:
    prompt = st.session_state.pop("pending_prompt")
    send_message(prompt)

if prompt := st.chat_input("Describe your symptoms, ask about medicines, diet plans, or find a doctor..."):
    send_message(prompt)
