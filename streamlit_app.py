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

# --- 3. WATERMARK (Branding) ---
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
    
    # Connection Status
    st.success("🟢 System Online")
    st.caption("Mode: Strict Digital-First")

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
    
    # --- THE "DIAMOND" SYSTEM PROMPT (Strict Rules) ---
    default_prompt = """You are the SSS Gingoog Virtual Assistant.

*** YOUR STRICT OPERATING PROTOCOLS ***

1. **PHASE 1: THE TRIAGE (ASK BEFORE ANSWERING)**
   - If the user asks a broad question (e.g., "How to apply for a loan?"), YOU MUST ASK CLARIFYING QUESTIONS FIRST.
   - Example: "To guide you correctly, are you an Employed, Voluntary, or OFW member?"
   - Do NOT dump generic information without knowing the member type.

2. **PHASE 2: DIGITAL-FIRST MANDATE (CRITICAL)**
   - **DEFAULT ACTION:** You must ALWAYS provide the Online/Mobile App procedure FIRST.
   - **PROHIBITION:** Do NOT mention Over-the-Counter (OTC) or Drop-box options unless the user explicitly mentions a problem.
   - *Exception:* If the service is NOT available online (e.g. UMID Biometrics, Funeral Claim for non-members), then and ONLY then can you suggest Branch filing.

3. **PHASE 3: EXEMPTION HANDLING**
   - If the user says "I cannot log in" or "My account is locked," immediately pivot to the Account Recovery / Branch Appointment protocol.

4. **PHASE 4: SOURCE OF TRUTH & SUPERSESSION**
   - **Search Order:** 1. Uploaded PDFs (Vault) -> 2. Permanent Database -> 3. www.sss.gov.ph (General Rules).
   - **Supersession Rule:** If [PDF A] is dated 2023 and [PDF B] is dated 2025, the 2025 document is the ONLY valid source. Ignore the old one.

5. **PHASE 5: ZERO HALLUCINATION**
   - If the answer is not in the Vault or SSS Website rules:
     "I cannot find a specific reference for this unique case. Please visit the SSS Gingoog Branch with your documents for a specialized assessment."

*** TONE: Professional, Direct, and Helpful. ***
"""
    if "system_instruction" not in st.session_state:
        st.session_state.system_instruction = default_prompt

    # ADMIN LOGIC
    stored_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
    
    if admin_pass == stored_password:
        st.success("Admin Logged In")
        
        # 1. BRAIN SURGERY (Edit the Prompt Live)
        with st.expander("🧠 **Customize Brain Instructions**", expanded=True):
            st.session_state.system_instruction = st.text_area("System Rules:", st.session_state.system_instruction, height=350)

        # 2. STICKY NOTE
        st.info("📝 **Sticky Note**")
        st.session_state.live_note = st.text_area("Updates:", st.session_state.live_note)
        
        # 3. THE VAULT (Upload)
        st.info("📂 **Upload Circulars/Charter**")
        uploaded_files = st.file_uploader("Add PDFs", type="pdf", accept_multiple_files=True)
        
        if uploaded_files:
            for pdf in uploaded_files:
                if pdf.name not in st.session_state.vault_files:
                    try:
                        reader = pypdf.PdfReader(pdf)
                        text = ""
                        for page in reader.pages: text += page.extract_text() + "\n"
                        st.session_state.vault_files[pdf.name] = text
                    except: pass
            if uploaded_files:
                st.success("✅ Files Indexed!")

        # 4. VAULT MANAGER (Delete Old Files)
        if st.session_state.vault_files:
            st.warning("📚 **Vault Contents:**")
            file_list = list(st.session_state.vault_files.keys())
            for fname in file_list:
                col1, col2 = st.columns([0.8, 0.2])
                col1.text(f"📄 {fname}")
                if col2.button("❌", key=f"del_{fname}"):
                    del st.session_state.vault_files[fname]
                    st.rerun()

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

# We use the Stable Model 'gemini-flash-latest' to match your scanner results
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

    # CONSTRUCT THE VAULT CONTENT
    vault_content = ""
    for fname, content in st.session_state.vault_files.items():
        vault_content += f"\n\n*** [DOCUMENT START: {fname}] ***\n{content}\n*** [DOCUMENT END] ***"

    full_prompt = f"""
    {st.session_state.system_instruction}
    
    *** THE VAULT (PRIORITY 1 - UPLOADED FILES) ***
    {vault_content if vault_content else "No files in Vault yet."}
    
    *** PERMANENT DATA (PRIORITY 2) ***
    {permanent_knowledge}
    
    *** URGENT ADMIN NOTES (PRIORITY 3) ***
    {st.session_state.live_note}
    
    *** EXTERNAL SOURCE (PRIORITY 4) ***
    www.sss.gov.ph (General Rules)
    
    *** USER QUESTION ***
    {prompt}
    """
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⏳ *Consulting protocols...*")
        
        try:
            # Short safety pause to prevent rapid-fire errors
            time.sleep(0.5)
            response = model.generate_content(full_prompt)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            if "429" in str(e):
                placeholder.error("⚠️ System Busy. Please wait 1 minute. (Admin: Create a New Project Key to fix this permanently)")
            else:
                placeholder.error(f"Connection Error: {str(e)}")
