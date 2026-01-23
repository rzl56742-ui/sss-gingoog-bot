import streamlit as st
import google.generativeai as genai
import pypdf
import time
import pandas as pd
from datetime import datetime

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

# --- 4. ANALYTICS ENGINE (NEW) ---
if "logs" not in st.session_state:
    st.session_state.logs = []

def log_interaction(user_question, ai_response):
    """
    Silently records the interaction for Admin Analytics.
    """
    # Simple Keyword Categorizer
    category = "General Inquiry"
    q_lower = user_question.lower()
    if any(x in q_lower for x in ["loan", "salary", "calamity"]): category = "Loans"
    elif any(x in q_lower for x in ["contri", "payment", "prn", "pay"]): category = "Contributions/Payment"
    elif any(x in q_lower for x in ["maternity", "sickness", "disability", "funeral", "death"]): category = "Benefit Claim"
    elif any(x in q_lower for x in ["register", "number", "umid", "id", "online", "password"]): category = "Registration/Account"
    
    # Save to Session State
    entry = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Category": category,
        "Question": user_question,
        "Response": ai_response[:100] + "..." # Save brief snippet
    }
    st.session_state.logs.append(entry)

# --- 5. SIDEBAR & ADMIN CONTROL ROOM ---
with st.sidebar:
    st.image("https://www.sss.gov.ph/sss/images/logo.png", width=100)
    st.title("Settings")
    st.success("🟢 System Online")
    st.caption("Mode: Advocate + Analytics")
    
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

*** INTERNAL LOGIC (FOLLOW SILENTLY) ***

1. **STEP 1: TRIAGE & DIAGNOSIS**
   - If question is broad, ASK CLARIFYING QUESTIONS FIRST (e.g. "Are you Employed or Voluntary?").

2. **STEP 2: DIGITAL-FIRST ADVOCACY (MANDATORY)**
   - **My.SSS App:** Instruct user to download the My.SSS App (Play Store).
   - **Online Default:** Provide ONLINE procedure first. NO OTC unless impossible.

3. **STEP 3: PAYMENT EDUCATION**
   - **PRN:** Instruct to generate PRN via App first.
   - **Partners:** Recommend: GCash, Maya, ShopeePay, Billeroo (https://new-sss.billeroo.com/cb7512de-356e-4471-80fd-1298eab0dbca), East Rural Bank, PNB-Gingoog, PeraHub.
   - **Value:** "Check My.SSS App for real-time posting."

4. **STEP 4: SOURCE CHECK**
   - Hierarchy: 1. Vault (PDFs) -> 2. SSS Website -> 3. Permanent Library.
   - Supersession: Newest PDF overrides old ones.

5. **STEP 5: ZERO HALLUCINATION**
   - If answer unknown: "Please visit our branch for specialized assessment."

*** OUTPUT: Natural, Professional. NO Headers like "Phase 1". ***
"""
    if "system_instruction" not in st.session_state:
        st.session_state.system_instruction = default_prompt

    # ADMIN LOGIC
    stored_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
    
    if admin_pass == stored_password:
        st.success("Admin Logged In")
        
        # TABBED INTERFACE FOR ADMIN
        tab1, tab2, tab3 = st.tabs(["📊 Analytics", "🧠 Brain", "📂 Data"])
        
        with tab1:
            st.subheader("📊 Session Insights")
            if st.session_state.logs:
                # Convert logs to DataFrame
                df = pd.DataFrame(st.session_state.logs)
                
                # Metric: Total Queries
                st.metric("Total Questions Asked", len(df))
                
                # Metric: Top Categories
                st.caption("Top Topics:")
                st.bar_chart(df["Category"].value_counts())
                
                # Download Button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Report (CSV)",
                    csv,
                    "sss_gingoog_analytics.csv",
                    "text/csv",
                    key='download-csv'
                )
            else:
                st.info("No data yet. Start asking questions!")

        with tab2:
            st.caption("Edit System Prompt")
            st.session_state.system_instruction = st.text_area("Rules:", st.session_state.system_instruction, height=200)

        with tab3:
            st.caption("Permanent Knowledge Generator")
            uploaded_files = st.file_uploader("Upload Circulars", type="pdf", accept_multiple_files=True)
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
                    st.success("✅ Converted!")
                    st.code(generated_text_block, language="text")

    st.markdown("---")
    st.caption("© 2026 SSS Gingoog Branch")

# --- 6. MAIN APP ---
st.title("SSS Gingoog Virtual Assistant") 
st.write("Your Digital Partner in Social Security.")
st.info("ℹ️ **Privacy Notice:** Do NOT enter your SSS Number, CRN, or personal details here.")

# --- 7. API SETUP ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ Critical Error: GOOGLE_API_KEY is missing from Streamlit Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

try:
    model = genai.GenerativeModel('gemini-flash-latest')
except Exception as e:
    st.error(f"Model Error: {e}")

# --- 8. CHAT LOGIC ---
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
        placeholder.markdown("⏳ *Checking SSS Digital Guidelines...*")
        
        try:
            time.sleep(0.5)
            response = model.generate_content(full_prompt)
            placeholder.markdown(response.text)
            
            # --- LOGGING HAPPENS HERE ---
            log_interaction(prompt, response.text)
            
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            if "429" in str(e):
                placeholder.error("⚠️ System Busy. Please wait 1 minute.")
            else:
                placeholder.error(f"Connection Error: {str(e)}")
