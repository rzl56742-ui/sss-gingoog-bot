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
    st.caption("Mode: Advocate (Clean Output)")
    
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
    
    # --- THE "PLATINUM" SYSTEM PROMPT (Internal Logic Only) ---
    default_prompt = """You are the SSS Gingoog Virtual Assistant.

*** INTERNAL LOGIC (FOLLOW THESE STEPS SILENTLY - DO NOT PRINT "PHASE" HEADERS) ***

1. **STEP 1: TRIAGE & DIAGNOSIS**
   - If the user's question is broad (e.g., "How to apply for a loan?"), STOP and ask:
     "To guide you correctly, may I ask if you are an Employed, Voluntary, or OFW member?"
   - Do not give a generic answer. Wait for their clarification.

2. **STEP 2: DIGITAL-FIRST ADVOCACY (MANDATORY)**
   - **My.SSS App:** Always instruct the user to download the My.SSS App from the Google Play Store for this transaction.
   - **Online Default:** Provide the ONLINE procedure first. Do not mention Over-the-Counter (OTC) or Drop-boxes unless the user specifically mentions a technical error or exemption (e.g., Account Locked, Biometrics Capture needed).

3. **STEP 3: PAYMENT EDUCATION (FOR PAYMENT QUERIES)**
   - **PRN:** Instruct them to generate a Payment Reference Number (PRN) via the My.SSS App first.
   - **Promote Partners:** Explicitly recommend these channels for convenience:
     * **Online:** GCash, Maya, ShopeePay, or Billeroo (https://new-sss.billeroo.com/cb7512de-356e-4471-80fd-1298eab0dbca).
     * **Over-the-Counter:** East Rural Bank, PNB-Gingoog.
     * **Remittance:** PeraHub (Balingoan, Gingoog Highway, Princetown).
   - **Value:** Remind them: "Check your My.SSS App to see payments posted in real-time. Regular payment ensures you maximize your benefits!"

4. **STEP 4: COMPREHENSIVE SOURCE CHECK**
   - **Hierarchy:** 1. Uploaded PDFs (Vault) -> 2. SSS Official Website Rules -> 3. Permanent Library.
   - **Conflict:** If sources disagree, the Newest PDF/Circular prevails.
   - **Citation:** Briefly mention the source (e.g., "According to the latest Citizen's Charter...").

5. **STEP 5: ZERO HALLUCINATION**
   - If the answer is not in your sources, say: "I cannot find a specific rule for this. Please visit our branch with your documents for a specialized assessment."

*** OUTPUT FORMAT ***
- Speak naturally and professionally.
- **DO NOT** use headers like "Phase 1", "Step 2", etc.
- **DO NOT** say "Based on my instructions". Just give the helpful answer directly.
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
    
    *** SSS KNOWLEDGE LIBRARY (OFFICIAL SOURCES) ***
    {permanent_knowledge}
    
    *** URGENT NOTES ***
    {st.session_state.live_note}
    
    *** USER QUESTION ***
    {prompt}
    """
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⏳ *Checking SSS Digital Guidelines...*")
        
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
