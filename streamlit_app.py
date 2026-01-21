import streamlit as st
import google.generativeai as genai
import pypdf

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
    if "ADMIN_PASSWORD" in st.secrets and admin_pass == st.secrets["ADMIN_PASSWORD"]:
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

# USE THE VERIFIED MODEL
try:
    model = genai.GenerativeModel('gemini-flash-latest')
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

# --- 10. HANDLE USER QUESTIONS (STRICT PROMPT LOGIC) ---
if prompt := st.chat_input("Mangutana ko (Ask here)..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        # --- THE STRICT SOURCE HIERARCHY ---
        
        full_knowledge_base = f"""
        *** DATA SOURCE 1: ADMIN UPLOADED FILES (HIGHEST PRIORITY) ***
        (This contains the latest Citizen's Charter and Circulars. USE THIS FIRST.)
        {st.session_state.pdf_knowledge}
        
        *** DATA SOURCE 2: PERMANENT DATABASE ***
        {permanent_knowledge}
        
        *** DATA SOURCE 3: URGENT ADMIN NOTES ***
        {st.session_state.live_note}
        """

        # STRICT INSTRUCTIONS FOR THE AI
        final_prompt = f"""
        You are the SSS Gingoog Virtual Assistant.
        
        *** YOUR STRICT INSTRUCTION MANUAL ***
        1. **SEARCH SOURCE 1 (PDFs) FIRST:** Look for the answer in the Admin Uploaded Files (Citizen's Charter/Circulars).
           - If found here, cite it: "According to the uploaded [File Name]..."
           
        2. **CROSS-REFERENCE:** If the user asks for a procedure or timeline, verify it against the Citizen's Charter in Source 1 if available.
        
        3. **OFFICIAL WEBSITE FALLBACK:** If the answer is NOT in Source 1 or Source 2, rely on your internal training specifically regarding **www.sss.gov.ph**.
           - You must state: "Based on general guidelines from www.sss.gov.ph..."
           
        4. **CLARIFICATION:** If the sources conflict, trust Source 1 (PDFs) as the latest truth.
        
        5. **TONE:** Professional, Direct, and Helpful. Use English or Visayan/Taglish as appropriate.
        
        *** KNOWLEDGE BASE ***
        {full_knowledge_base}
        
        *** USER QUESTION ***
        {prompt}
        """
        
        with st.spinner("Checking Citizen's Charter & SSS Website..."):
            response = model.generate_content(final_prompt)
            
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"⚠️ Connection Error: {str(e)}")
