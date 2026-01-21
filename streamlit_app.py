import streamlit as st
import google.generativeai as genai

st.title("🔍 Connection & Model Scanner")

# 1. Check if Key exists
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ Critical Error: API Key is missing from Secrets.")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"]
st.write(f"🔑 **Key Check:** The app sees a key starting with `{api_key[:4]}...`")

# 2. Try to connect to Google
try:
    genai.configure(api_key=api_key)
    st.info("📡 Contacting Google Servers...")
    
    # 3. Ask Google for the list of models
    models = genai.list_models()
    available_models = []
    
    for m in models:
        # We only want models that can chat (generateContent)
        if "generateContent" in m.supported_generation_methods:
            available_models.append(m.name)
            
    if available_models:
        st.success(f"✅ SUCCESS! We found {len(available_models)} working models.")
        st.markdown("### 📋 Copy one of these exact names:")
        st.code("\n".join(available_models))
    else:
        st.warning("⚠️ Connected to Google, but no Chat models were found. This usually means the API Key has no permissions.")

except Exception as e:
    st.error(f"❌ Connection Failed completely. Error details:")
    st.code(str(e))
