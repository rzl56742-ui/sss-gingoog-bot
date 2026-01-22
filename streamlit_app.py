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
    st.caption("Mode: Digital Advocate")
    
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
    
    # --- THE "DIGITAL ADVOCATE" SYSTEM PROMPT ---
    default_prompt = """You are the SSS Gingoog Virtual Assistant.

*** YOUR STRICT OPERATING PROTOCOLS ***

1. **PHASE 1: THE TRIAGE**
   - If the user asks a broad question, ASK CLARIFYING QUESTIONS FIRST (e.g. "Are you Employed or Voluntary?").

2. **PHASE 2: DIGITAL PROMOTION (MANDATORY)**
   - **My.SSS App:** Always promote downloading the My.SSS App from the Google Play Store.
   - **Real-Time Monitoring:** Educate members that they can check their Contribution and Loan payments in REAL-TIME using the App.
   - **Value Statement:** Encourage members to pay contributions regularly to avail of full SSS benefits.

3. **PHASE 3: PAYMENT PROTOCOLS**
   - **PRN First:** For payment inquiries, instruct them to generate a Payment Reference Number (PRN) via the My.SSS App.
   - **Promote Channels:** Explicitly recommend these convenient partners near us:
     * **E-Wallets:** GCash, Maya, ShopeePay.
     * **Online:** Billeroo (https://new-sss.billeroo.com/cb7512de-356e-4471-80fd-1298eab0dbca).
     * **Over-the-Counter:** East Rural Bank, PNB-Gingoog.
     * **Remittance Centers:** PeraHub Balingoan, PeraHub Gingoog Highway, PeraHub Princetown.

4. **PHASE 4: SOURCE OF TRUTH (NEW HIERARCHY)**
   - **Priority 1:** SSS Website Rules & Citizen's Charter (Uploaded PDFs).
   - **Priority 2:** Permanent Knowledge (Stored Library).
   - **Supersession:** Newer documents always override older ones.

5. **PHASE 5: ZERO HALLUCINATION**
   - If answer is unknown, direct to SSS Gingoog Branch.
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

        # 2. PERMANENT KNOWLEDGE GENERATOR
        st.info("📂 **Add to Permanent Database**")
        uploaded_files = st.file_uploader("Upload Circulars/Charter", type="pdf", accept_multiple_files=True)
        
        if uploaded_files:
            generated_text_block = ""
            for pdf in uploaded_files:
                try:
                    reader = pypdf.PdfReader(pdf)
                    text = ""
                    for page in reader.pages: text += page.extract_text() + "\n"
                    generated_text_block += f"\n\n[DOCUMENT: {pdf.name}]\n{text}\n"
                except: pass
            
            if generated_text_block:
                st.success("✅ Conversion Complete!")
                st.warning("👉 Copy text below -> Paste to 'sss_knowledge.py' on GitHub.")
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
    
    *** SSS KNOWLEDGE LIBRARY ***
    {permanent_knowledge}
    
    *** URGENT NOTES ***
    {st.session_state.live_note}
    
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
