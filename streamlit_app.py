import streamlit as st
import google.generativeai as genai

# Page Configuration
st.set_page_config(page_title="SSS Gingoog Virtual Assistant", page_icon="🤖")

st.title("SSS Gingoog Virtual Consultant")
st.write("Your Digital Partner in Social Security.")

# 1. Setup the Google Connection
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Please add your GOOGLE_API_KEY to Streamlit Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 2. Setup the Model (Using the NEW one found in your list)
model = genai.GenerativeModel('gemini-2.0-flash')

# 3. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Handle User Input
if prompt := st.chat_input("Mangutana ko (Ask here)..."):
    # Show user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate and show response
    try:
        response = model.generate_content(prompt)
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"An error occurred: {e}")
