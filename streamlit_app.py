import streamlit as st
import google.generativeai as genai
import pypdf
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SSS Gingoog Virtual Assistant", page_icon="🤖", layout="centered")

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
    
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    
    # Admin Panel
    st.subheader("🔒 Admin Access")
    admin_pass = st.text_input("Enter Admin Key", type="password")
    
    if "pdf_knowledge" not in st.session_state: st.session_state.pdf_knowledge = ""
    if "live_note" not in st.session_state: st.session_state.live_note = ""

    # Check Password
    stored_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
    if admin_pass == stored_password:
        st.success("Admin Logged In")
        st.info("📝 **Sticky Note**")
        st.session_state.live_note = st.text_area("Urgent Updates:", st.session_state.live_note)
        
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

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ Key Missing in Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 6. THE "LITE" MODEL SWITCHER ---
def get_response_with_fallback(prompt_input):
    """
    Attempts to use the Lite model first. If that fails, tries the Flash model.
    """
    # PRIORITY 1: The "Lite" model (Fast, usually empty traffic)
    # Found in your scanner list: image_f49d71.png
    primary_model = "gemini-2.0-flash-lite-preview-02-05"
    
    # PRIORITY 2: The standard fallback
    backup_model = "gemini-flash-latest"

    try:
        model = genai.GenerativeModel(primary_model)
        response = model.generate_content(prompt_input)
        return response.text
    except Exception as e1:
        # If Lite fails, try Backup immediately
        try:
            time.sleep(1) # Brief pause
            model = genai.GenerativeModel(backup_model)
            response = model.generate_content(prompt_input)
            return response.text
        except Exception as e2:
            # If BOTH fail, return the specific error to help us debug
            return f"SYSTEM_ERROR: {str(e1)} || {str(e2)}"

# --- 7. CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Maayong adlaw! I am your SSS Gingoog Virtual Assistant. Unsa ang akong matabang nimo karon?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Mangutana ko (Ask here)..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Build Prompt
    full_prompt = f"""
    You are the SSS Gingoog Virtual Assistant.
    
    SOURCES:
    1. UPLOADED PDFS: {st.session_state.pdf_knowledge}
    2. PERMANENT DATA: {permanent_knowledge}
    3. ADMIN NOTES: {st.session_state.live_note}
    
    INSTRUCTIONS:
    - Search Uploaded PDFs first.
    - Fallback to SSS.gov.ph rules.
    - Be professional.
    
    QUESTION: {prompt}
    """
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⏳ *Connecting...*")
        
        # Execute with Fallback
        result = get_response_with_fallback(full_prompt)
        
        # Check for our custom error tag
        if "SYSTEM_ERROR" in result:
            placeholder.error("⚠️ connection failed.")
            with st.expander("Show Technical Details (For Admin)"):
                st.code(result) # This will show us EXACTLY why it failed
        else:
            placeholder.markdown(result)
            st.session_state.messages.append({"role": "assistant", "content": result})
