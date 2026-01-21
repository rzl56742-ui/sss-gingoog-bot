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

# --- 3. WATERMARK (RPT / SSSGingoog) ---
st.markdown("""
<style>
.watermark {
    position: fixed;
    bottom: 40px; 
    right: 20px;
    z-index: 9999;
    color: rgba(255, 255, 255, 0.5);
    font-size: 14px;
    font-family: sans-serif;
    font-weight: bold;
    pointer-events: none;
}
</style>
<div class="watermark">RPT / SSSGingoog</div>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR (ADMIN & SETTINGS) ---
with st.sidebar:
    st.image("https://www.sss.gov.ph/sss/images/logo.png", width=100)
    st.title("Settings")
    
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    
    # --- ADMIN LOGIN SECTION ---
    st.subheader("🔒 Admin Access")
    admin_pass = st.text_input("Enter Admin Key", type="password")
    
    # Initialize Session States
    if "pdf_knowledge" not in st.session_state:
        st.session_state.pdf_knowledge = ""
    if "live_note" not in st.session_state:
        st.session_state.live_note = ""

    # ADMIN LOGIC
    stored_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
    
    if admin_pass == stored_password:
        st.success("Admin Authenticated")
        
        # A. LIVE TEXT NOTES
        st.info("📝 **Quick Updates (Sticky Note)**")
        st.session_state.live_note = st.text_area(
            "Type urgent updates here:", 
            value=st.session_state.live_note
        )

        # B. PDF UPLOADER
        st.info("📂 **Upload Citizen's Charter / Circulars**")
        uploaded_files = st.file_uploader("Upload PDF Files", type="pdf", accept_multiple_files=True)
        
        if uploaded_files:
            pdf_text_accumulator = ""
            for pdf in uploaded_files:
                try:
                    reader = pypdf.PdfReader(pdf)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    pdf_text_accumulator += f"\n[SOURCE: PDF - {pdf.name}]\n{text}\n"
                except Exception as e:
                    st.error(f"Error reading {pdf.name}: {e}")
            
            # Save extracted text
            if pdf_text_accumulator:
                st.session_state.pdf_knowledge = pdf_text_accumulator
                st.success(f"✅ Indexed {len(uploaded_files)} PDF documents!")

    st.markdown("---")
    st.caption("© 2026 SSS Gingoog Branch")

# --- 5. MAIN APP INTERFACE ---
st.title("SSS Gingoog Virtual Assistant") 
st.write("Your Digital Partner in Social Security.")

# --- 6. PRIVACY NOTICE ---
st.info("ℹ️ **Privacy Notice:** Do NOT enter your SSS Number, CRN, or personal details here.")

# --- 7. API CONNECTION CHECK ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ Critical Error: GOOGLE_API_KEY is missing from Streamlit Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- MODEL SETUP ---
# We use gemini-2.0-flash as it appeared in your scanner list
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    st.error(f"Model Error: {e}")

# --- 8. CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Maayong adlaw! I am your SSS Gingoog Virtual Assistant. Unsa ang akong matabang nimo karon? (How can I help you today?)"
    })

# --- 9. DISPLAY CHAT ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 10. HANDLE USER QUESTIONS (WITH AUTO-RETRY) ---
if prompt := st.chat_input("Mangutana ko (Ask here)..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Prepare the Prompt
    full_knowledge_base = f"""
    *** DATA SOURCE 1: ADMIN UPLOADED FILES (HIGHEST PRIORITY) ***
    {st.session_state.pdf_knowledge}
    
    *** DATA SOURCE 2: PERMANENT DATABASE ***
    {permanent_knowledge}
    
    *** DATA SOURCE 3: URGENT ADMIN NOTES ***
    {st.session_state.live_note}
    """

    final_prompt = f"""
    You are the SSS Gingoog Virtual Assistant.
    
    *** INSTRUCTIONS ***
    1. Search Uploaded PDFs FIRST.
    2. Fallback to SSS.gov.ph guidelines if not found.
    3. Be professional and clear.
    
    *** KNOWLEDGE BASE ***
    {full_knowledge_base}
    
    *** USER QUESTION ***
    {prompt}
    """
    
    # --- AUTO-RETRY LOGIC (The Smart Part) ---
    response_text = ""
    retry_count = 0
    max_retries = 3
    
    with st.spinner("Checking SSS References..."):
        while retry_count < max_retries:
            try:
                # Try to get the answer
                response = model.generate_content(final_prompt)
                response_text = response.text
                break # If successful, stop the loop!
                
            except Exception as e:
                # If error is about Quota (429), wait and try again
                if "429" in str(e):
                    retry_count += 1
                    time.sleep(4) # Wait 4 seconds before trying again
                    if retry_count == max_retries:
                        st.error("⚠️ System Busy: Too many requests. Please wait 1 minute.")
                else:
                    st.error(f"Error: {e}")
                    break

    # If we got an answer, show it
    if response_text:
        with st.chat_message("assistant"):
            st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
