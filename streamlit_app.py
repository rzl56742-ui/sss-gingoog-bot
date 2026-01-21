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
    # We now use a DICTIONARY to store files individually: {'filename': 'text_content'}
    if "vault_files" not in st.session_state: st.session_state.vault_files = {}
    if "live_note" not in st.session_state: st.session_state.live_note = ""
    
    # --- THE BRAIN: SUPERSESSION PROTOCOL ---
    default_prompt = """You are the SSS Gingoog Virtual Assistant.

*** CORE PROTOCOLS ***
1. **ONLINE-FIRST MANDATE:** ALWAYS assume the member must file ONLINE (My.SSS/Mobile App). Only discuss OTC if the case is an exemption.
2. **DIAGNOSTIC MODE:** Ask clarifying questions first if the inquiry is vague (e.g., "Are you Employed or Voluntary?").

*** CONFLICT RESOLUTION & SUPERSESSION PROTOCOL (CRITICAL) ***
The "Vault" contains multiple circulars/documents. You must determine which is active:
1. **CHECK DATES:** If [Document A] is dated 2022 and [Document B] is dated 2024, and they discuss the same topic, **[Document B] PREVAILS.**
2. **LOOK FOR "SUPERSEDES":** If a document explicitly says "This supersedes Circular X", treat Circular X as **OBSOLETE** and ignore its rules.
3. **REPORTING:** If you find conflicting info, answer based on the NEWEST document and briefly mention: *"Based on the latest issuance [New Doc Name], which updates the previous policy..."*
"""
    if "system_instruction" not in st.session_state:
        st.session_state.system_instruction = default_prompt

    # ADMIN LOGIC
    stored_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
    
    if admin_pass == stored_password:
        st.success("Access Granted")
        
        # 1. CUSTOMIZE BRAIN
        with st.expander("🧠 **Customize Brain**"):
            st.session_state.system_instruction = st.text_area("System Rules:", st.session_state.system_instruction, height=200)

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
                        # Store in Dictionary
                        st.session_state.vault_files[pdf.name] = text
                    except: pass
            if uploaded_files:
                st.success("✅ Files Indexed!")

        # 4. VAULT MANAGEMENT (DELETE OBSOLETE FILES)
        if st.session_state.vault_files:
            st.warning("📚 **Manage Vault Library:**")
            st.caption("Delete files that are clearly obsolete to help the AI.")
            
            # Create a list of keys to avoid runtime error during deletion
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
    model = genai.GenerativeModel('gemini-flash-latest') # Using stable model
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

    # CONSTRUCT THE VAULT CONTENT DYNAMICALLY
    # We label each file clearly so the AI can compare them
    vault_content = ""
    for fname, content in st.session_state.vault_files.items():
        vault_content += f"\n\n*** [DOCUMENT START: {fname}] ***\n{content}\n*** [DOCUMENT END] ***"

    full_prompt = f"""
    {st.session_state.system_instruction}
    
    *** THE VAULT (PRIORITY SOURCES) ***
    {vault_content if vault_content else "No files in Vault yet."}
    
    *** PERMANENT KNOWLEDGE ***
    {permanent_knowledge}
    
    *** URGENT NOTES ***
    {st.session_state.live_note}
    
    *** USER QUESTION ***
    {prompt}
    """
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⏳ *Analyzing Vault for latest policies...*")
        
        try:
            time.sleep(0.5)
            response = model.generate_content(full_prompt)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            if "429" in str(e):
                placeholder.error("⚠️ Traffic Limit. Please wait 1 minute. (Admin: Consider New Project Key)")
            else:
                placeholder.error(f"Connection Error: {str(e)}")
