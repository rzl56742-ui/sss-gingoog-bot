import streamlit as st
import google.generativeai as genai
import pypdf # This is the new tool we just added

# --- IMPORT PERMANENT KNOWLEDGE ---
try:
    from sss_knowledge import data as permanent_knowledge
except ImportError:
    permanent_knowledge = ""

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="SSS Gingoog Virtual Assistant", page_icon="🤖", layout="centered")

# --- WATERMARK ---
st.markdown("""
<style>
.watermark {
    position: fixed; bottom: 40px; right: 20px; z-index: 9999;
    color: rgba(255, 255, 255, 0.5); font-size: 14px; font-weight: bold; pointer-events: none;
}
</style>
<div class="watermark">RPT / SSSGingoog</div>
""", unsafe_allow_html=True)

# --- SIDEBAR & ADMIN PANEL ---
with st.sidebar:
    st.image("https://www.sss.gov.ph/sss/images/logo.png", width=100)
    st.title("Settings")
    
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    
    # ADMIN LOGIN
    st.subheader("🔒 Admin Access")
    admin_pass = st.text_input("Enter Admin Key", type="password")
    
    # Initialize session state for PDF text
    if "pdf_knowledge" not in st.session_state:
        st.session_state.pdf_knowledge = ""

    if "ADMIN_PASSWORD" in st.secrets and admin_pass == st.secrets["ADMIN_PASSWORD"]:
        st.success("Access Granted")
        st.info("📝 **Upload New Circulars (PDF)**")
        
        # FILE UPLOADER WIDGET
        uploaded_files = st.file_uploader("Upload PDF Files", type="pdf", accept_multiple_files=True)
        
        if uploaded_files:
            extracted_text = ""
            for pdf in uploaded_files:
                try:
                    # Read the PDF
                    reader = pypdf.PdfReader(pdf)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    extracted_text += f"\n--- START OF FILE: {pdf.name} ---\n{text}\n--- END OF FILE ---\n"
                except Exception as e:
                    st.error(f"Error reading {pdf.name}: {e}")
            
            # Save the text to the brain
            if extracted_text:
                st.session_state.pdf_knowledge = extracted_text
                st.success(f"✅ Successfully read {len(uploaded_files)} PDF file(s)!")
                
    st.caption("© 2026 SSS Gingoog Branch")

# --- MAIN APP ---
st.title("SSS Gingoog Virtual Consultant")
st.write("Your Digital Partner in Social Security.")
st.info("ℹ️ **Privacy Notice:** Do NOT enter your SSS Number, CRN, or personal details here.")

# --- API SETUP ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ GOOGLE_API_KEY missing.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
try:
    model = genai.GenerativeModel('gemini-flash-latest')
except:
    st.error("Model error. Check API Key.")

# --- CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Maayong adlaw! Unsa ang akong matabang nimo karon?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Mangutana ko (Ask here)..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        # COMBINE: Permanent + Admin PDF Uploads
        full_knowledge = f"""
        PERMANENT DATABASE:
        {permanent_knowledge}
        
        TEMPORARY PDF UPLOADS (FROM ADMIN):
        {st.session_state.pdf_knowledge}
        """

        full_prompt = f"""
        You are a helpful SSS Gingoog Consultant.
        USE THIS KNOWLEDGE BASE TO ANSWER:
        {full_knowledge}
        
        USER QUESTION: {prompt}
        Answer clearly in English/Visayan.
        """
        
        with st.spinner("Checking SSS Files..."):
            response = model.generate_content(full_prompt)
            
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"Error: {e}")
