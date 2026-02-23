import os
import streamlit as st
import google.generativeai as genai

# 1. Set up the UI first
st.set_page_config(page_title="AI Healthcare Assistant", page_icon="🩺")
st.title("🩺 AI Healthcare Assistant")

# --- Location Sidebar ---
user_city = st.sidebar.selectbox(
    "📍 Select your current city:",
    ["Bangalore", "Mumbai", "Delhi", "Chennai"]
)

# 2. Secure API Key Loading (Works locally and on Streamlit Cloud)
try:
    # Tries to get the key from Streamlit Cloud Secrets
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    # If testing on your Mac, grabs it from your local .env file
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

# 3. Define the AI Model (Using the ultra-stable 1.5 Flash model)
system_instruction = """
You are a helpful and cautious AI Healthcare Assistant. You can provide general dietary advice, check mild symptoms, and give standard information on medicines. 
CRITICAL RULE: Always include a short disclaimer that you are an AI and the user must consult a real doctor for medical advice.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=system_instruction
)

# 4. Initialize Chat Memory
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.chat_session = model.start_chat(history=[])

# Display existing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. The Main Chat Loop
if prompt := st.chat_input("Describe your symptoms, ask for a diet plan, or find a doctor..."):
    
    # Show user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Smart routing for doctor recommendations
    contextual_prompt = prompt
    keywords = ["doctor", "specialist", "hospital", "clinic", "pain", "injury"]
    
    if any(word in prompt.lower() for word in keywords):
        contextual_prompt += f"\n\n[System Note: The user needs medical care in {user_city}. Recommend 2-3 real, top-rated hospitals or clinics in {user_city} that specialize in their symptoms.]"
        
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                response = st.session_state.chat_session.send_message(contextual_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error("Whoops! The server is busy. Give it a few seconds and try again.")
