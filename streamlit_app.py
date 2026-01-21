import streamlit as st
import google.generativeai as genai

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SSS Gingoog Virtual Assistant",
    page_icon="🤖",
    layout="centered"
)

# --- 2. WATERMARK (CSS) ---
# This puts the "RPT/SSSGingoog" mark in the bottom right corner
st.markdown("""
<style>
.watermark {
    position: fixed;
    bottom: 10px;
    right: 10px;
    opacity: 0.5;
    z-index: 99;
    color: grey;
    font-size: 12px;
    font-family: sans-serif;
    font-weight: bold;
    pointer-events: none; /* Allows clicking through the text */
}
</style>
<div class="watermark">RPT/SSSGingoog</div>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR (CONTROLS) ---
with st.sidebar:
    st.image("https://www.sss.gov.ph/sss/images/logo.png", width=100) # Optional: SSS Logo if available, or just text
    st.title("Settings")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.caption("© 2024 SSS Gingoog Branch")

# --- 4. MAIN APP HEADER ---
st.title("SSS Gingoog Virtual Consultant")
st.write("Your Digital Partner in Social Security.")

# --- 5. PRIVACY NOTICE (CRITICAL) ---
# The blue box warning users not to share sensitive info
st.info("ℹ️ **Privacy Notice:** Do NOT enter your SSS Number, CRN, or personal details here.")

# --- 6. API & MODEL SETUP ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ Critical Error: GOOGLE_API_KEY is missing from Streamlit Secrets.")
    st.stop()

# Configure the API
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# USE THE WORKING MODEL (From your Scanner results)
try:
    model = genai.GenerativeModel('gemini-flash-latest')
except Exception as e:
    st.error(f"Error loading model: {e}")

# --- 7. CHAT HISTORY MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add an initial greeting from the bot
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Maayong adlaw! I am your SSS Virtual Assistant. Unsa ang akong matabang nimo karon? (How can I help you today?)"
    })

# --- 8. DISPLAY CHAT ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 9. HANDLE USER INPUT ---
if prompt := st.chat_input("Mangutana ko (Ask here)..."):
    # Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate Response
    try:
        # We act as a persona
        full_prompt = f"You are a helpful and professional SSS (Social Security System) Consultant for the Gingoog Branch. Answer the following inquiry clearly and politely: {prompt}"
        
        with st.spinner("Thinking..."):
            response = model.generate_content(full_prompt)
            
        # Display Assistant message
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"⚠️ Connection Error: {str(e)}")
        st.markdown("Please try again in a few seconds.")
