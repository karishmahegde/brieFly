import requests.auth
import streamlit as st
import streamlit.components.v1 as components
import requests
import urllib.parse
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import base64

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

# --- Utility ---
def token_expiry_check():
    if "token_time" not in st.session_state:
        return True
    return datetime.now() - st.session_state["token_time"] > timedelta(hours=1)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8501")

st.set_page_config(page_title="brieFly", page_icon="./assets/icon.png", layout="centered")

# Convert image to base64
def get_base64_image(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Load your image (JPG or PNG)
img_base64 = get_base64_image("assets/background.png")  # or .png

# Inject CSS
page_bg_img = f"""
<style>
.stApp {{
    background-image: url("data:image/png;base64,{img_base64}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

.stAppHeader {{
    background: transparent !important;
}}
</style>
"""

st.markdown(page_bg_img, unsafe_allow_html=True)

st.markdown("""
    <div style='text-align: center; font-size: 2.5rem; font-weight: bold; color: rgb(249, 202, 218;'>🐝 brieFly</div>
    <br/>
    <div style='text-align: center; font-size: 1.5rem; font-weight: normal; color: #FFCE44;'>
        Your AI-powered meeting assistant for smarter recaps and action tracking
    </div>
    <div style='text-align: center; color: rgba(250, 250, 250, 0.7);'>
        Upload your meeting recording or connect your Zoom account to get a concise summary, action items, and sentiment insights — all in a click!
    </div>
""", unsafe_allow_html=True)

st.markdown("#####")

# --- Buttons ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    ch1, ch2 = st.columns(2)

    with ch1:
        login_clicked = st.button("🎥 Zoom Recordings")
        st.markdown("<p style='text-align:center; color:rgba(250, 250, 250, 0.6); font-size: 0.8rem;'>Connect your Zoom account to fetch <span style='color:#FFCE44;'>cloud recordings</span> directly.</p>", unsafe_allow_html=True)

    with ch2:
        if "upload_clicked" not in st.session_state:
            st.session_state.upload_clicked = False

        if st.button("📁 Upload a File"):
            st.session_state.upload_clicked = True
        st.markdown("<p style='text-align:center; color:rgba(250, 250, 250, 0.6); font-size: 0.8rem;'>Upload a .mp3, .m4a, .vtt, or .txt file to analyze your meeting instantly.</p>", unsafe_allow_html=True)

st.markdown("---")  

# --- Handle Zoom redirect code (when returning from Zoom auth) ---
if "access_token" not in st.session_state and "code" in st.query_params:
    code = st.query_params["code"]
    token_url = "https://zoom.us/oauth/token"
    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    response = requests.post(token_url, auth=auth, data=payload)

    if response.status_code == 200:
        token_data = response.json()
        st.session_state["access_token"] = token_data["access_token"]
        st.session_state["token_time"] = datetime.now()
        st.success("✅ Zoom has successfully authenticated!")
        st.query_params.clear()
    else:
        st.error("❌ Failed to exchange code for token.")
        st.text(response.text)  

# --- Start Zoom OAuth Flow ---
if "access_token" not in st.session_state:
    if login_clicked:
        st.session_state.upload_clicked = False
        auth_url = (
            "https://zoom.us/oauth/authorize"
            f"?response_type=code&client_id={CLIENT_ID}"
            f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        )
        zoom_logo_url = "https://img.icons8.com/color/48/zoom.png"  # You can replace this if needed
        zoom_login_button = f"""
        <style>
            .zoom-login-btn{{
                display: inline-flex;
                align-items: center;
                padding: 0.50rem 0.75rem;
                background-color: rgb(19, 23, 32);
                border: 1px solid rgba(250, 250, 250, 0.2);
                border-radius: 0.5rem;
                text-decoration: none;
                font-weight: 500;
                font-size: 16px;
                margin-top: 10px;
                text-decoration: none!important;
                color: white!important;
            }}
            .zoom-login-btn:hover{{
                border-color: rgb(255, 75, 75);
                color: rgb(255, 75, 75)!important;
                text-decoration: none;
            }}

        </style>
        <a href="{auth_url}" class="zoom-login-btn" target="_self"> <img src="{zoom_logo_url}" alt="Zoom" width= 25px height = 25px style="margin-right: 5px;">
            Login to Zoom
        </a>
        """
        col1, col2, col3 = st.columns([1,2, 1])
        with col2:
            st.markdown(zoom_login_button, unsafe_allow_html=True)

# --- Upload a file ---
if st.session_state.upload_clicked:
    upload_file = st.file_uploader("Upload your .mp3/.m4a/.txt/.vtt file", type=["mp3", "m4a", "vtt", "txt"])

    if st.button("📤 Upload"):
        if upload_file is None:
            st.error("No file selected.")
        else:
            upload_dir = "recordings"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, upload_file.name)

            with open(file_path, "wb") as f:
                f.write(upload_file.read())

            st.success(f"✅ File successfully uplaoded and ready for transcription")
            st.audio(file_path, format="audio/m4a") #Display an audio player for the uploaded file
            st.session_state["audio_path"] = file_path  # Save path for Whisper

# --- Fetch Recordings ---
if "access_token" in st.session_state and not st.session_state.upload_clicked:
    if st.button("Fetch My Recordings"):
        if token_expiry_check():
            st.warning("😵 Session expired. Please log in again.")
        else:
            from backend.get_zoom_recordings import fetch_recordings
            recordings = fetch_recordings(st.session_state["access_token"])
            if recordings:
                st.write("📼 Your Zoom Recordings:")
                for rec in recordings:
                    topic = rec.get("topic", "Untitled Meeting")
                    start_time_raw = rec.get("start_time")
                    start_time = datetime.strptime(start_time_raw, "%Y-%m-%dT%H:%M:%SZ")
                    formatted_date = start_time.strftime("%B %Y")  # e.g., May 2025

                    duration = rec.get("duration", 0)  # In minutes
                    hours = duration // 60
                    minutes = duration % 60
                    if hours:
                        duration_str = f"{hours}h {minutes}m"
                    else:
                        duration_str = f"{minutes} minutes"

                    download_url = rec.get("download_url")

                    st.markdown(
                        f"**{topic} – {formatted_date}** ({duration_str}) – [Download Link]({download_url})"
                    )
            else:
                st.warning("No recordings found.")