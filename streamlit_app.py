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
    
    # --- THE STRICT BRAIN PROTOCOL ---
    # This is the instruction manual you asked for.
    default_prompt = """You are the SSS Gingoog Virtual Assistant.

*** YOUR PRIME DIRECTIVES (STRICTLY FOLLOW) ***

1. **PHASE 1: DIAGNOSIS (CLARIFY FIRST)**
   - Do not guess. If the user asks a vague question (e.g., "How to apply for loan?"), YOU MUST ASK:
     "To guide you correctly, are you an Employed, Voluntary, or OFW member?"
   - If they mention a claim, ask: "Is this for Sickness, Maternity, or Retirement?"

2. **PHASE 2: DIGITAL-FIRST MANDATE**
   - Check if the service is available on My.SSS or Mobile App.
   - **IF YES:** Provide the ONLINE procedure immediately. Do NOT mention Over-the-Counter (OTC) yet.
   - **IF NO:** Only discuss OTC if the service is IMPOSSIBLE online.

3. **PHASE 3: EXEMPTION HANDLING**
   - Only offer OTC/Branch Walk-in if:
     a) The user explicitly says they have a technical error/account lock.
     b) The procedure requires physical biometrics (e.g., UMID capture).
     c) It is a specialized claim (e.g., Death claim disputes).

4. **PHASE 4: SOURCE OF TRUTH & SUPERSESSION**
   - **HIERARCHY:** 1. Uploaded PDFs (The Vault) -> 2. Permanent Data -> 3. www.sss.gov.ph (General Rules).
   - **SUPERSESSION:** If PDF A (2022) and PDF B (2025) conflict, **OBEY PDF B (2025)**.
   - **CITATION:** Always mention your source: "According to Circular [Number]..." or "Based on guidelines from www.sss.gov.ph..."

5. **PHASE 5: ZERO HALLUCINATION (FALLBACK)**
   - If the answer is NOT in the Vault and NOT in standard SSS rules:
     **DO NOT INVENT AN ANSWER.**
   - Instead, say: "I cannot find a specific reference for this unique case. Please visit the SSS Gingoog Branch and bring your relevant documents so our officer can assess your record personally."

*** TONE: Professional, Helpful, Advocate-Educator. ***
"""
    if "system_instruction" not in st.session_state:
        st.session_state.system_instruction = default_prompt

    # ADMIN LOGIC
    stored_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
    
    if admin_pass == stored_password:
        st.success("Access Granted")
        
        # 1. CUSTOMIZE BRAIN
        with st.expander("🧠 **Customize Brain**"):
            st.session_state.system_instruction = st.text_area("System Rules:", st.session_state.system_instruction, height=350)

        # 2. STICKY NOTE
        st.info("📝 **Sticky Note**")
        st.session_state.live_note = st.text_area("Updates:", st.session_state.live_note)
        
        # 3. THE VAULT (SMART UPLOAD)
        st.info("📂 **Upload to Vault**")
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

        # 4. VAULT MANAGEMENT
        if st.session_state.vault_files:
            st.warning("📚 **Manage Vault Library:**")
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
        vault_content += f"\n\n*** [DOCUMENT: {fname}] ***\n{content}\n*** [END DOCUMENT] ***"

    full_prompt = f"""
    {st.session_state.system_instruction}
    
    *** THE VAULT (PRIORITY 1) ***
    {vault_content if vault_content else "No files in Vault yet."}
    
    *** PERMANENT DATA (PRIORITY 2) ***
    {permanent_knowledge}
    
    *** URGENT NOTES (PRIORITY 3) ***
    {st.session_state.live_note}
    
    *** GENERAL KNOWLEDGE FALLBACK ***
    Use www.sss.gov.ph rules if not found above.
    
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
                placeholder.error("⚠️ System Busy. Please wait 1 minute.")
            else:
                placeholder.error(f"Connection Error: {str(e)}")
