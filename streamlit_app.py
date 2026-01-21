import streamlit as st
import google.generativeai as genai

# --- IMPORT YOUR KNOWLEDGE BASE ---
# This looks for the sss_knowledge.py file you just created
try:
    from sss_knowledge import data as sss_knowledge_base
except ImportError:
    sss_knowledge_base = "No specific knowledge base found. Please use general SSS knowledge."

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SSS Gingoog Virtual Assistant",
    page_icon="🤖",
    layout="centered"
)

# --- 2. WATERMARK ---
st.markdown("""
<style>
.watermark {
    position: fixed;
    bottom: 40px; 
    right: 20px;
    z-index: 9999;
    color: rgba(255, 255, 255, 0.5);
    font-size: 14px;
    font-family: sans-serif;
    font-weight: bold;
    pointer-events: none;
}
</style>
<div class="watermark">RPT / SSSGingoog</div>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("Settings")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.caption("© 2026 SSS Gingoog Branch")

# --- 4. MAIN APP HEADER ---
st.title("SSS Gingoog Virtual Consultant")
st.write("Your Digital Partner in Social Security.")

# --- 5. PRIVACY NOTICE ---
st.info("ℹ️ **Privacy Notice:** Do NOT enter your SSS Number, CRN, or personal details here.")

# --- 6. API & MODEL SETUP ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ Critical Error: GOOGLE_API_KEY is missing from Streamlit Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

try:
    model = genai.GenerativeModel('gemini-flash-latest')
except Exception as e:
    st.error(f"Error loading model: {e}")

# --- 7. CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []
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
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        # --- HERE IS THE SECRET SAUCE ---
        # We inject the knowledge base directly into the prompt
        full_prompt = f"""
        You are a helpful and professional SSS (Social Security System) Consultant for the Gingoog Branch.
        
        USE THIS KNOWLEDGE BASE TO ANSWER:
        {sss_knowledge_base}
        
        USER QUESTION: {prompt}
        
        Answer clearly and politely in mixed English/Visayan if appropriate.
        """
        
        with st.spinner("Checking SSS Guidelines..."):
            response = model.generate_content(full_prompt)
            
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"⚠️ Connection Error: {str(e)}")
