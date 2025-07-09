import streamlit as st
from dotenv import load_dotenv
import os
from PIL import Image
import pytesseract
import docx
import PyPDF2
import requests
import json
import base64

# # Load and encode background image
# with open("images/back2.jpg", "rb") as img_file:
#     encoded = base64.b64encode(img_file.read()).decode()

# Place this at the very top, before any other Streamlit commands
st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background: whiete;
        background-size: cover !important;
        font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif !important;
        font-size: 16px !important;
    }}

.stButton > button {{
    background-color: green !important;
    color: white !important;
    border-radius: 6px !important;
    border: none !important;
}}
.stButton > button:hover {{
    background-color: darkgreen !important;
}}


.header-row {{
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 18px;
    margin-top: 8px;
    width: 100%;
}} 
.header {{
    color: #4F8BF9;
    font-weight: 800;
    font-size: 2rem;
    # letter-spacing: 0.5px;
    font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif !important;
    # margin: 0 18px 0 0;
}}
.sub {{
    font-size: 2.2rem;
    color: #e74c3c;
    font-weight: 700;
    cursor: pointer;
    transition: color 0.2s, background 0.2s;
    # padding: 2px 14px;
    border-radius: 6px;
}}
.sub:hover {{
    background: #f8d7da;
    color: #c0392b;
}}

    .footer {{
        text-align: center;
        color: #999999;
        margin-top: 32px;
        font-size: em;
    }}
    .stTextInput, .stFileUploader, .stButton {{
    div[data-testid="stFileUploader"] > label > div,
    div[data-testid="stFileUploader"] span,
    div[data-testid="stFileUploader"] > label > span,
    div[data-testid="stFileUploader"] > label > small,
    div[data-testid="stFileUploader"] > label > small > span {{
        font-size: 16px !important;
    }}
    div[data-testid="stFileUploaderDropzoneInstructions"] {{
        display: none !important;
    }}
    div[data-testid="stFileUploader"] svg {{
        display: none !important;
    }}
   
    .history-btn {{
        background: green;
        color: green;
        border-radius: 6px;
        border: none;
        padding: 6px 18px;
        font-size: 15px;
        margin-bottom: 12px;
        margin-right: 8px;
        cursor: pointer;
        transition: background 0.2s;
    }} 
    .history-btn:hover {{
        background: green;
    }}
    .element-container .stTextInput, .element-container .stFileUploader, .element-container .stButton {{
        font-size: 16px !important;
    }}
    </style>
""", unsafe_allow_html=True)

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = "gemini-2.0-flash"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1/models/{MODEL}:generateContent?key={API_KEY}"

def extract_text_from_file(uploaded_file):
    file_type = uploaded_file.type
    if file_type == "text/plain":
        return uploaded_file.read().decode("utf-8")
    elif file_type == "application/pdf":
        reader = PyPDF2.PdfReader(uploaded_file)
        return "".join([page.extract_text() or "" for page in reader.pages])
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif file_type.startswith("image/"):
        image = Image.open(uploaded_file)
        return pytesseract.image_to_string(image)
    return None

def get_gemini_response(prompt):
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    response = requests.post(ENDPOINT, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        try:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return "❌ Error: Could not parse model response."
    else:
        return f"❌ API Error: {response.status_code} - {response.text}"

st.set_page_config(page_title="Gemini Chat", page_icon="MyGpt", layout="centered")
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
st.markdown(
    '<div class="header-row">'
    '<div class="header">Google-</div>'
    '<div class="sub">GenerativeAI</div>'
    '</div>',
    unsafe_allow_html=True
)

# --- Chat history state ---
if 'file_text' not in st.session_state:
    st.session_state['file_text'] = None
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# --- Horizontal row: chat input, file uploader, send button (aligned and sized) ---
import streamlit as st

# Create three columns for the widgets
col1, col2, col3 = st.columns([5, 2, 1])  # Adjust ratios as needed

with col1:
    user_input = st.text_area(
        "",
        value="",
        key="user_input",
        height=100,
        placeholder="Enter your message..."
        # increase font size of text area=22px
        # , label_visibility="visible"
        , label_visibility="visible"
    )
with col2:
    uploaded_file = st.file_uploader(
        "",
        key="file_uploader",
        # width=100%

        type=["txt", "pdf", "docx", "jpg", "jpeg", "png"],
        label_visibility="visible"
    )
with col3:
    "",
    st.markdown("<div style='height: 100%;'></div>", unsafe_allow_html=True)  # Spacer
    send = st.button("➤", key="send", help="Send", use_container_width=True, type="primary")
    label_visibility = "visible"

if uploaded_file:
    file_text = extract_text_from_file(uploaded_file)
    st.session_state['file_text'] = file_text
    st.info("File uploaded. All answers will now be based on the file until you clear it.")

# --- Chat logic and history ---
if send and user_input:
    if st.session_state['file_text']:
        prompt = (
            f"Given this file content:\n{st.session_state['file_text'][:4000]}\n\n"
            f"User's question: {user_input}\n\n"
            f"Answer based only on the file."
        )
    else:
        prompt = user_input
    with st.spinner("Thinking..."):
        answer = get_gemini_response(prompt)
    st.session_state['chat_history'].append(("You", user_input))
    st.session_state['chat_history'].append(("Gemini", answer))
    st.markdown(f"<div style='font-size:16px;'><b>Gemini:</b> {answer}</div>", unsafe_allow_html=True)

# --- Collapsible chat history with save and clear buttons ---
st.markdown("<br>", unsafe_allow_html=True)
with st.expander(" Chat History", expanded=False):
    if st.session_state['chat_history']:
        for role, msg in st.session_state['chat_history']:
            st.markdown(f"<b style='color:#4F8BF9;font-size:20px'>{role}:</b> <span style='font-size:20px'>{msg}</span>", unsafe_allow_html=True)
        # Save history button
        if st.button("Save History", key="save_history", help="Download chat history as txt", type="primary"):
            chat_lines = [f"{role}: {msg}" for role, msg in st.session_state['chat_history']]
            chat_txt = "\n".join(chat_lines)
            st.download_button("Download Chat History", chat_txt, file_name="gemini_chat_history.txt")
        # delete history button
        if st.button("Clear Chat History", key="clear_history", help="Clear chat history", type="primary"):
            st.session_state['chat_history'] = []
            st.info("Chat history cleared.")
        # reset chat history button
        if st.button("Reset Chat", key="reset_chat", help="Reset the chat and clear history", type="primary"):
            st.session_state['chat_history'] = []
            st.session_state['file_text'] = None
            st.info("Chat reset. Back to normal chat.")
    else:
        st.info("No chat history yet.")

# --- File context clear button ---
if st.session_state['file_text']:
    if st.button("Clear File Context"):
        st.session_state['file_text'] = None
        st.info("File context cleared. Back to normal chat.")

st.markdown(
    '<div class="footer">This Gpt made using the Api key of Google generativeai.</div>',
    unsafe_allow_html=True
)
st.markdown("</div>", unsafe_allow_html=True)
