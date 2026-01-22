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

# --- 4. SIDEBAR & ADMIN CONTROL ROOM ---
with st.sidebar:
    st.image("https://www.sss.gov.ph/sss/images/logo.png", width=100)
    st.title("Settings")
    st.success("🟢 System Online")
    
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    
    # --- ADMIN ACCESS ---
    st.subheader("🔒 Admin Access")
    admin_pass = st.text_input("Enter Admin Key", type="password")
    
    # Initialize Session States
    if "vault_files" not in st.session_state: st.session_state.vault_files = {}
    if "live_note" not in st.session_state: st.session_state.live_note = ""
    
    # --- SYSTEM PROMPT (STRICT) ---
    default_prompt = """You are the SSS Gingoog Virtual Assistant.

*** YOUR STRICT OPERATING PROTOCOLS ***
1. **PHASE 1: THE TRIAGE**
   - If the user asks a broad question, ASK CLARIFYING QUESTIONS FIRST (e.g. "Are you Employed or Voluntary?").

2. **PHASE 2: DIGITAL-FIRST MANDATE**
   - DEFAULT: Provide Online/Mobile App procedure FIRST.
   - PROHIBITION: Do NOT mention OTC unless the service is IMPOSSIBLE online.

3. **PHASE 3: SOURCE OF TRUTH**
   - Search Order: 1. Permanent Knowledge (Vault) -> 2. SSS Website.
   - Supersession: Newer documents override older ones.

4. **PHASE 4: ZERO HALLUCINATION**
   - If answer is unknown, direct to official SSS website wwww.sss.gov.ph and SSS Gingoog Branch.
"""
    if "system_instruction" not in st.session_state:
        st.session_state.system_instruction = default_prompt

    # ADMIN LOGIC
    stored_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
    
    if admin_pass == stored_password:
        st.success("Admin Logged In")
        
        # 1. BRAIN SURGERY
        with st.expander("🧠 **Customize Brain**"):
            st.session_state.system_instruction = st.text_area("System Rules:", st.session_state.system_instruction, height=200)

        # 2. PERMANENT KNOWLEDGE GENERATOR (THE FIX)
        st.info("📂 **Add to Permanent Database**")
        st.caption("Upload PDFs here to convert them into permanent text code.")
        uploaded_files = st.file_uploader("Upload Circulars/Charter", type="pdf", accept_multiple_files=True)
        
        if uploaded_files:
            generated_text_block = ""
            for pdf in uploaded_files:
                try:
                    reader = pypdf.PdfReader(pdf)
                    text = ""
                    for page in reader.pages: text += page.extract_text() + "\n"
                    # Create a clean block for the knowledge file
                    generated_text_block += f"\n\n[DOCUMENT: {pdf.name}]\n{text}\n"
                except: pass
            
            if generated_text_block:
                st.success("✅ Conversion Complete!")
                st.warning("👉 **ACTION REQUIRED: Copy the text below and paste it into 'sss_knowledge.py' on GitHub to make it 100% PERMANENT.**")
                st.code(generated_text_block, language="text")

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

    # COMBINE SOURCES
    full_prompt = f"""
    {st.session_state.system_instruction}
    
    *** PERMANENT KNOWLEDGE VAULT (PRIORITY 1) ***
    {permanent_knowledge}
    
    *** URGENT NOTES (PRIORITY 2) ***
    {st.session_state.live_note}
    
    *** EXTERNAL SOURCE (PRIORITY 3) ***
    www.sss.gov.ph
    
    *** USER QUESTION ***
    {prompt}
    """
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⏳ *Consulting protocols...*")
        
        try:
            time.sleep(0.5)
            response = model.generate_content(full_prompt)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            if "429" in str(e):
                placeholder.error("⚠️ System Busy. Please wait 1 minute. (Admin: Create a New Project Key)")
            else:
                placeholder.error(f"Connection Error: {str(e)}")
