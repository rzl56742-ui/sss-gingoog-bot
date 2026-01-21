import streamlit as st
import google.generativeai as genai
import pypdf
import time

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(
    page_title="SSS Gingoog Virtual Assistant",
    page_icon="🤖",
    layout="centered"
)

# --- 2. IMPORT PERMANENT KNOWLEDGE (FAIL-SAFE) ---
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

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image("https://www.sss.gov.ph/sss/images/logo.png", width=100)
    st.title("Settings")
    
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    
    # --- ADMIN ACCESS ---
    st.subheader("🔒 Admin Access")
    admin_pass = st.text_input("Enter Admin Key", type="password")
    
    # Data States
    if "pdf_knowledge" not in st.session_state: st.session_state.pdf_knowledge = ""
    if "live_note" not in st.session_state: st.session_state.live_note = ""

    # Admin Logic
    stored_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
    if admin_pass == stored_password:
        st.success("Access Granted")
        st.info("📝 **Sticky Note**")
        st.session_state.live_note = st.text_area("Urgent Updates:", value=st.session_state.live_note)
        
        st.info("📂 **Upload PDFs**")
        uploaded_files = st.file_uploader("Upload Circulars/Charter", type="pdf", accept_multiple_files=True)
        if uploaded_files:
            text_acc = ""
            for pdf in uploaded_files:
                try:
                    reader = pypdf.PdfReader(pdf)
                    for page in reader.pages: text_acc += page.extract_text() + "\n"
                except: pass
            if text_acc:
                st.session_state.pdf_knowledge = text_acc
                st.success("✅ PDFs Indexed!")

    st.markdown("---")
    st.caption("© 2026 SSS Gingoog Branch")

# --- 5. MAIN APP ---
st.title("SSS Gingoog Virtual Assistant") 
st.write("Your Digital Partner in Social Security.")
st.info("ℹ️ **Privacy Notice:** Do NOT enter your SSS Number, CRN, or personal details here.")

# --- 6. INTELLIGENT MODEL SWITCHER (THE FIX) ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ Key Missing.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def get_smart_response(prompt_text):
    """
    Tries multiple models in sequence. If one is busy/broken, 
    it automatically jumps to the next one.
    """
    # The "Relay Team" of models to try (Priority Order)
    # These names are taken from your scanner results
    model_team = [
        "gemini-2.0-flash",       # 1. Smartest & Fastest
        "gemini-flash-latest",    # 2. Reliable Backup
        "gemini-2.0-flash-exp",   # 3. Experimental Backup
        "gemini-pro"              # 4. Old Faithful
    ]
    
    last_error = ""
    
    for model_name in model_team:
        try:
            # Try to load and run the current model
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt_text)
            return response.text # Success! Return immediately.
            
        except Exception as e:
            # If failed, log error and continue loop
            last_error = str(e)
            time.sleep(1) # Brief pause before switching
            continue
            
    # If ALL models fail, then we show the error
    raise Exception(f"All servers busy. Last error: {last_error}")

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
    
    *** PRIORITY SOURCES ***
    1. UPLOADED PDFS: {st.session_state.pdf_knowledge}
    2. PERMANENT DATA: {permanent_knowledge}
    3. ADMIN NOTES: {st.session_state.live_note}
    
    *** INSTRUCTIONS ***
    - Check Priority Sources first.
    - If not found, use general SSS website knowledge (www.sss.gov.ph).
    - Be professional and clear.
    
    *** QUESTION ***
    {prompt}
    """

    # Generate with Fallback System
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("🔄 *Connecting to SSS Database...*")
        
        try:
            # Use the new smart function
            response_text = get_smart_response(full_prompt)
            placeholder.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
        except Exception as e:
            placeholder.error("⚠️ Network Traffic is extremely high. Please wait 2 minutes.")
