import streamlit as st
import google.generativeai as genai

# --- IMPORT YOUR PERMANENT KNOWLEDGE BASE ---
try:
    from sss_knowledge import data as permanent_knowledge
except ImportError:
    permanent_knowledge = ""

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

# --- 3. SIDEBAR (ADMIN PANEL RESTORED) ---
with st.sidebar:
    st.image("https://www.sss.gov.ph/sss/images/logo.png", width=100)
    st.title("Settings")
    
    # CLEAR CONVERSATION BUTTON
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    
    # --- ADMIN ACCESS SECTION ---
    st.subheader("🔒 Admin Access")
    admin_pass = st.text_input("Enter Admin Key", type="password")
    
    # Check if the password matches the one in Secrets
    if "ADMIN_PASSWORD" in st.secrets and admin_pass == st.secrets["ADMIN_PASSWORD"]:
        st.success("Access Granted")
        
        # LIVE KNOWLEDGE INJECTOR
        st.info("📝 **Live Knowledge Update**")
        st.caption("Paste new Circulars or updates here for immediate use. (Note: These reset if the app reboots. Update sss_knowledge.py for permanent storage.)")
        
        if "live_knowledge" not in st.session_state:
            st.session_state.live_knowledge = ""
            
        # Text area for Admin to type new info
        new_update = st.text_area("Add Temporary Info:", value=st.session_state.live_knowledge, height=150)
        st.session_state.live_knowledge = new_update
        
    else:
        if admin_pass: # Only show error if they typed something wrong
            st.error("Incorrect Key")

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
        # COMBINE PERMANENT KNOWLEDGE + LIVE ADMIN UPDATES
        current_live_info = st.session_state.get("live_knowledge", "")
        
        full_knowledge_base = f"""
        PERMANENT DATABASE:
        {permanent_knowledge}
        
        URGENT UPDATES (FROM ADMIN):
        {current_live_info}
        """

        # INJECT INTO PROMPT
        full_prompt = f"""
        You are a helpful and professional SSS (Social Security System) Consultant for the Gingoog Branch.
        
        USE THIS KNOWLEDGE BASE TO ANSWER:
        {full_knowledge_base}
        
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
