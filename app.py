import os
import sqlite3
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from db_setup import setup_database
setup_database()
# 1. Load API key securely
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 2. Set up the Streamlit Page
st.set_page_config(page_title="AI Healthcare Assistant", page_icon="🩺")
st.title("🩺 AI Healthcare Assistant")
# --- Location Sidebar ---
user_city = st.sidebar.selectbox(
    "📍 Select your current city:",
    ["Bangalore", "Mumbai", "Delhi", "Chennai"]
)
# 3. Define the AI Persona
system_instruction = """
You are a helpful and cautious AI Healthcare Assistant. You can provide general dietary advice, check mild symptoms, and give standard information on medicines. 
CRITICAL RULES:
1. Always include a short disclaimer that you are an AI and the user must consult a real doctor for medical advice.
2. If the user asks for a doctor recommendation, use the local directory information provided in the prompt context to suggest a specialist.
"""

# Initialize the Gemini Model
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=system_instruction
)

# Pass the selected city into the function
def get_local_doctors(city):
    conn = sqlite3.connect('healthcare.db')
    cursor = conn.cursor()
    # Dynamic SQL WHERE clause
    cursor.execute("SELECT doctor_name, specialty, hospital_clinic, location, contact_number FROM doctors WHERE city = ?", (city,))
    doctors = cursor.fetchall()
    conn.close()
    
    doc_list = []
    for doc in doctors:
        doc_list.append(f"- {doc[0]} ({doc[1]}) at {doc[2]}, {doc[3]}. Contact: {doc[4]}")
    return "\n".join(doc_list)

# 5. Initialize Streamlit Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.chat_session = model.start_chat(history=[])

# Display existing chat history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. The Main Chat Loop
if prompt := st.chat_input("Describe your symptoms, ask for a diet plan, or find a doctor..."):
    
    # Display user prompt in UI
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add to UI history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Check if we need to query the doctor database
    contextual_prompt = prompt
    keywords = ["doctor", "specialist", "hospital", "clinic", "pain", "injury"]
if any(word in prompt.lower() for word in keywords):
        # Fetch doctors only for the selected city
        doctor_data = get_local_doctors(user_city)
        contextual_prompt += f"\n\n[System Note: The user may need a doctor. Here is the local directory for {user_city}:\n{doctor_data}\nRecommend a suitable one if applicable.]"
        # Inject the database results invisibly into the prompt
        contextual_prompt += f"\n\n[System Note: The user may need a doctor. Here is the local directory:\n{doctor_data}\nRecommend a suitable one if applicable.]"
        
# 6. The Main Chat Loop
if prompt := st.chat_input("Describe your symptoms, ask for a diet plan, or find a doctor..."):
    
    # Display user prompt in UI
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add to UI history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Check if we need to query the doctor database
    contextual_prompt = prompt
    keywords = ["doctor", "specialist", "hospital", "clinic", "pain", "injury"]
    if any(word in prompt.lower() for word in keywords):
        # Fetch doctors only for the selected city
        doctor_data = get_local_doctors(user_city)
        contextual_prompt += f"\n\n[System Note: The user may need a doctor. Here is the local directory for {user_city}:\n{doctor_data}\nRecommend a suitable one if applicable.]"
        
    # Get response from Gemini
    with st.chat_message("assistant"):
        with st.spinner("Analyzing symptoms..."):
            response = st.session_state.chat_session.send_message(contextual_prompt)
        st.markdown(response.text)
        
    # Add response to UI history
    st.session_state.messages.append({"role": "assistant", "content": response.text})
