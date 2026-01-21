import streamlit as st
import google.generativeai as genai

# --- CONFIGURATION & BRANDING ---
st.set_page_config(page_title="SSS Gingoog Virtual Assistant", page_icon="🏢", layout="wide")

# Persistent State for "White Label" Settings
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = "You are a helpful SSS Assistant." # Default, will be overwritten by Admin
if "signature_name" not in st.session_state:
    st.session_state.signature_name = "SSS Gingoog"

# --- SIDEBAR (ADMIN CONTROL ROOM) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/4/46/Social_Security_System_%28Philippines%29.svg", width=100)
    st.markdown("### 🔒 Admin Access")
    
    # Simple Password Protection for Admin Panel
    admin_password = st.text_input("Admin Key", type="password")
    
    if admin_password == st.secrets["ADMIN_PASSWORD"]:
        st.success("Admin Logged In")
        st.markdown("---")
        st.markdown("### 🧠 Brain Surgery (Prompts)")
        
        # Admin can edit the Bot's logic here
        new_prompt = st.text_area("Edit System Instructions:", value=st.session_state.system_prompt, height=300)
        if st.button("Update Brain"):
            st.session_state.system_prompt = new_prompt
            st.success("Bot Logic Updated!")
            
        st.markdown("---")
        st.markdown("### ✍️ Signature Manager")
        # Admin can change the signature
        new_sig = st.text_input("Conversation Closer:", value=st.session_state.signature_name)
        if st.button("Update Signature"):
            st.session_state.signature_name = new_sig
            st.success("Signature Updated!")
            
        st.markdown("---")
        st.markdown("### 📚 Knowledge Upload")
        uploaded_file = st.file_uploader("Upload Circulars/PDFs", type=['txt', 'pdf', 'csv'])
        if uploaded_file:
            st.info("File upload logic connects here (Requires advanced vector storage for large files). For now, paste text content into the Prompt area for immediate learning.")

# --- MAIN CHAT INTERFACE ---
st.title("SSS Gingoog Virtual Consultant")
st.markdown("**Your Digital Partner in Social Security.**")
st.info("ℹ️ **Privacy Notice:** Do NOT enter your SSS Number, CRN, or personal details here.")

# Initialize API (Using Secrets)
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("API Key not found. Please set it in Streamlit Secrets.")

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle User Input
if prompt := st.chat_input("Mangutana ko (Ask here)..."):
    # Display User Message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Combine System Prompt + User Prompt for the AI
    full_prompt = f"{st.session_state.system_prompt}\n\nUSER QUERY: {prompt}\n\nRemember to sign off as: {st.session_state.signature_name}"

    try:
        # Generate Response
        response = model.generate_content(full_prompt)
        bot_reply = response.text
        
        # Display Bot Message
        with st.chat_message("assistant"):
            st.markdown(bot_reply)
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        
    except Exception as e:
        st.error(f"System Error: {e}. Please try again.")

# --- FOOTER (PERMANENT WATERMARK) ---
st.markdown("---")
st.markdown(
    """
    <div style='position: fixed; bottom: 10px; right: 10px; opacity: 0.7; font-size: 12px; background-color: white; padding: 5px; border-radius: 5px; border: 1px solid #ccc;'>
    Developed by <b>RPT/SSSGingoog</b>
    </div>
    """,
    unsafe_allow_html=True
)
