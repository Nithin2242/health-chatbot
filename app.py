import os
import sqlite3
import streamlit as st
import google.generativeai as genai

# 1. Load API key securely
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 2. Set up the Streamlit Page
st.set_page_config(page_title="AI Healthcare Assistant", page_icon="🩺")
st.title("🩺 AI Healthcare Assistant")

# 3. Sidebar
with st.sidebar:
    st.header("What I can help with")
    st.markdown("- 🩻 Symptom checker\n- 🥗 Diet & nutrition plans\n- 🏥 Find local doctors\n- 💊 General medicine info")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

# 4. Define the AI Persona
system_instruction = """
You are a helpful and cautious AI Healthcare Assistant. You can provide general dietary advice, check mild symptoms, and give standard information on medicines. 
CRITICAL RULES:
1. Always include a short disclaimer that you are an AI and the user must consult a real doctor for medical advice.
2. If the user asks for a doctor recommendation, use the local directory information provided in the prompt context to suggest a specialist.
"""

# Initialize the Gemini Model
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=system_instruction
)

# 5. Helper function to fetch doctors from SQLite database
def init_db():
    conn = sqlite3.connect('healthcare.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS doctors 
                   (doctor_name TEXT, specialty TEXT, 
                    hospital_clinic TEXT, location TEXT, contact_number TEXT)''')
    cursor.execute("SELECT COUNT(*) FROM doctors")
    if cursor.fetchone()[0] == 0:
        sample_doctors = [
            ("Dr. Priya Sharma", "General Physician", "Apollo Clinic", "Bangalore", "080-12345678"),
            ("Dr. Rajan Mehta", "Cardiologist", "Fortis Hospital", "Bangalore", "080-87654321"),
            ("Dr. Anita Rao", "Neurologist", "Manipal Hospital", "Bangalore", "080-11223344"),
            ("Dr. Suresh Kumar", "Dermatologist", "Columbia Asia", "Bangalore", "080-55667788"),
            ("Dr. Meena Iyer", "Nutritionist", "Narayana Health", "Bangalore", "080-99887766"),
        ]
        cursor.executemany("INSERT INTO doctors VALUES (?,?,?,?,?)", sample_doctors)
    conn.commit()
    conn.close()

def get_local_doctors():
    conn = sqlite3.connect('healthcare.db')
    cursor = conn.cursor()
    cursor.execute("SELECT doctor_name, specialty, hospital_clinic, location, contact_number FROM doctors")
    doctors = cursor.fetchall()
    conn.close()
    doc_list = []
    for doc in doctors:
        doc_list.append(f"- {doc[0]} ({doc[1]}) at {doc[2]}, {doc[3]}. Contact: {doc[4]}")
    return "\n".join(doc_list)

# Init DB on startup
init_db()

# 6. Initialize Streamlit Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])

# Display existing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Show example prompts if chat is empty
if not st.session_state.messages:
    st.markdown("**Try asking:**")
    cols = st.columns(3)
    examples = ["I have a headache", "Suggest a diet plan", "Find a cardiologist"]
    for col, ex in zip(cols, examples):
        if col.button(ex):
            st.session_state.messages.append({"role": "user", "content": ex})
            st.rerun()

# 7. Main Chat Loop
if prompt := st.chat_input("Describe your symptoms, ask for a diet plan, or find a doctor..."):

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Check if doctor lookup is needed
    contextual_prompt = prompt
    keywords = ["find a doctor", "specialist", "recommend a doctor", "which doctor", "hospital"]
    if any(word in prompt.lower() for word in keywords):
        doctor_data = get_local_doctors()
        contextual_prompt += f"\n\n[System Note: Here is the local doctor directory:\n{doctor_data}\nRecommend a suitable one if applicable.]"

 import time

# Get response from Gemini — with retry logic
response = None
with st.chat_message("assistant"):
    with st.spinner("Thinking..."):
        for attempt in range(3):  # Try up to 3 times
            try:
                response = st.session_state.chat_session.send_message(contextual_prompt)
                st.markdown(response.text)
                break  # Success — exit the loop
            except Exception as e:
                error_msg = str(e)
                if "ResourceExhausted" in error_msg or "429" in error_msg:
                    if attempt < 2:
                        wait_time = (attempt + 1) * 10  # 10s, then 20s
                        st.warning(f"⏳ Rate limit hit. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        st.error("⚠️ Still rate limited. Please wait 1 minute and try again.")
                elif "InvalidArgument" in error_msg:
                    st.error("⚠️ Invalid request. Please rephrase your message.")
                    break
                else:
                    st.error("⚠️ Something went wrong. Please try again.")
                    break
