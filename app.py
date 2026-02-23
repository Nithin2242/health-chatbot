import os
import sqlite3
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

# --- Initialize Database ---
from db_setup import setup_database
setup_database()

# 1. Load API key securely (Bulletproof Cloud Method)
load_dotenv()
try:
    # Force Streamlit to read the fresh key from the Cloud Secrets
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    # Fallback to local .env if running on your Mac
    api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

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
"""

# Initialize the Gemini Model (DOWNGRADED TO A MORE STABLE SERVER)
model = genai.GenerativeModel(
    model_name="models/gemini-1.5-flash",
    system_instruction=system_instruction
)

# 4. Initialize Streamlit Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.chat_session = model.start_chat(history=[])

# Display existing chat history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. The Main Chat Loop
if prompt := st.chat_input("Describe your symptoms, ask for a diet plan, or find a doctor..."):
    
    # Display user prompt in UI
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add to UI history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Check if we need to trigger a dynamic doctor recommendation
    contextual_prompt = prompt
    keywords = ["doctor", "specialist", "hospital", "clinic", "pain", "injury"]
    
    if any(word in prompt.lower() for word in keywords):
        # Instruct Gemini to dynamically determine the specialty and find real hospitals
        contextual_prompt += f"\n\n[System Note: The user is looking for medical care in {user_city}. First, identify the exact medical specialty required for their specific symptoms. Then, use your extensive knowledge base to recommend 2-3 real, top-rated hospitals or clinics in {user_city} that specialize in this area.]"
        
    # Get response from Gemini
    with st.chat_message("assistant"):
        with st.spinner("Analyzing symptoms..."):
            response = st.session_state.chat_session.send_message(contextual_prompt)
        st.markdown(response.text)
        
    # Add response to UI history
    st.session_state.messages.append({"role": "assistant", "content": response.text})
