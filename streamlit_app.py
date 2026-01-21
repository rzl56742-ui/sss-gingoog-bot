import streamlit as st
import google.generativeai as genai
import pypdf
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="SSS Gingoog Virtual Assistant",
    page_icon="🤖",
    layout="centered"
)

# --- 2. FAIL-SAFE KNOWLEDGE IMPORT ---
try:
    from sss_knowledge import data as permanent_knowledge
except ImportError:
    permanent_knowledge = ""

# --- 3. WATERMARK ---
st.markdown("""
<style>
.watermark {
    position: fixed; bottom: 40px; right: 20px; z-index: 9999;
    color: rgba(255, 255, 255, 0.5); font-size: 14px; font-weight: bold; pointer-events: none;
}
</style>
<div class="watermark">RPT / SSSGingoog</div>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR & ADMIN ---
with st.sidebar:
    st.image("https://www.sss.gov.ph/sss/images/logo.png", width=100)
    st.title("Settings")
    
    # System Status Indicator
    st.success("🟢 System Online")
    st.caption("Model: gemini-flash-latest")
    
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    
    # Admin Panel
    st.subheader("🔒 Admin Access")
    admin_pass = st.text_input("Enter Admin Key", type="password")
    
    if "pdf_knowledge" not in st.session_state: st.session_state.pdf_knowledge = ""
    if "live_note" not in st.session_state: st.session_state.live_note = ""

    stored_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
    if admin_pass == stored_password:
        st.success("Admin Logged In")
        st.info("📝 **Sticky Note**")
        st.session_state.live_note = st.text_area("Updates:", st.session_state.live_note)
        
        st.info("📂 **Upload PDFs**")
        uploaded_files = st.file_uploader("Upload Circulars", type="pdf", accept_multiple_files=True)
        if uploaded_files:
            acc_text = ""
            for pdf in uploaded_files:
                try:
                    reader = pypdf.PdfReader(pdf)
                    for page in reader.pages: acc_text += page.extract_text() + "\n"
                except: pass
            if acc_text:
                st.session_state.pdf_knowledge = acc_text
                st.success("✅ PDFs Indexed!")
    
    st.markdown("---")
    st.caption("© 2026 SSS Gingoog Branch")

# --- 5. MAIN APP ---
st.title("SSS Gingoog Virtual Assistant") 
st.write("Your Digital Partner in Social Security.")
st.info("ℹ️ **Privacy Notice:** Do NOT enter your SSS Number, CRN, or personal details here.")

# --- 6. API SETUP ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ Critical Error: GOOGLE_API_KEY is missing from Streamlit Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# SWITCHING TO THE STABLE MODEL (From your Scanner List)
# This is less likely to be 'Busy' than the 2.0 version
try:
    model = genai.GenerativeModel('gemini-flash-latest')
except Exception as e:
    st.error(f"Model Error: {e}")

# --- 7. CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Maayong adlaw! I am your SSS Gingoog Virtual Assistant. Unsa ang akong matabang nimo karon?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Mangutana ko (Ask here)..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Prepare Context
    full_prompt = f"""
    You are the SSS Gingoog Virtual Assistant.
    
    SOURCES:
    1. UPLOADS: {st.session_state.pdf_knowledge}
    2. PERMANENT DATA: {permanent_knowledge}
    3. NOTES: {st.session_state.live_note}
    
    INSTRUCTIONS:
    - Check Uploads/Notes first.
    - Fallback to SSS.gov.ph.
    - Be professional.
    
    QUESTION: {prompt}
    """
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⏳ *Thinking...*")
        
        try:
            # We add a small safety pause to prevent double-firing
            time.sleep(0.5)
            response = model.generate_content(full_prompt)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            # Detailed Error Handling
            err_msg = str(e)
            if "429" in err_msg:
                placeholder.error("⚠️ Traffic Limit. Please wait 1 minute. (Tip: Create a Key in a NEW Project to fix this permanently)")
            elif "404" in err_msg:
                placeholder.error("⚠️ Model Not Found. Please verify API Key permissions.")
            else:
                placeholder.error(f"Connection Error: {err_msg}")
