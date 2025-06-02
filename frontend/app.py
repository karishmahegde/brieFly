"""
brieFly: An AI-powered Streamlit app that fetches Zoom recordings or user-uploaded audio/text files,
transcribes them using OpenAI Whisper, summarizes content via GPT-4, analyzes sentiment using RoBERTa,
and generates contextual suggestions for team managers.
"""

import os
import requests.auth
import streamlit as st
import requests
import urllib.parse
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import base64

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()   #Load the variables from the .env file

def zoom_token_check():   #Zoom API Tokens expire after 1 hour | To check if the token is valid or expired
    if "token_time" not in st.session_state:
        return True
    return datetime.now() - st.session_state["token_time"] > timedelta(hours=1) #timedelta represents number of hours

#Zoom variables
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8501")

#Configures the default settings of the page.
st.set_page_config(page_title="brieFly", page_icon="./assets/icon.png", layout="centered")

# --- Setting Background Image - START ---
# Convert image to base64
def get_base64_image(path):
    """
    Reads an image file and encodes it into base64 format for CSS embedding.
    Args:
        path (str): Path to the image file.
    Returns:
        str: Base64-encoded string of the image.
    """
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

img_base64 = get_base64_image("assets/background.png")

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
# --- Setting Background Image - END ---

#Title & Description
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

st.markdown("#####")    #Vertical space

#Options - Zoom Login or File Upload
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
if "access_token" not in st.session_state and "code" in st.query_params:    #If access token is not yet fetched and redicrect code is available
    code = st.query_params["code"]      #Redirect code given by Zoom
    token_url = "https://zoom.us/oauth/token"
    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    response = requests.post(token_url, auth=auth, data=payload)    #Fetching the token using the code

    if response.status_code == 200:
        token_data = response.json()
        st.session_state["access_token"] = token_data["access_token"]
        st.session_state["token_time"] = datetime.now() #Recording the time token was issued to later check if it's valid
        st.success("✅ Zoom has successfully authenticated!")
        st.query_params.clear() #Clear the one-time-use code
    else:
        st.error("❌ Failed to exchange code for token.")
        st.text(response.text)  

# --- Start Zoom OAuth Flow ---
if "access_token" not in st.session_state: 
    if login_clicked:
        st.session_state.upload_clicked = False #Setting variables for file upload to false to prevent related elements from showing up
        st.session_state.pop("audio_path", None)
        auth_url = (    #URL to fetch the one-time-use code
            "https://zoom.us/oauth/authorize"
            f"?response_type=code&client_id={CLIENT_ID}"
            f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        )
        zoom_logo_url = "https://img.icons8.com/color/48/zoom.png"      #Login with Zoom button
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
        col1, col2, col3 = st.columns([1,2, 1]) #Display the button in the center
        with col2:
            st.markdown(zoom_login_button, unsafe_allow_html=True)

# --- Upload a file ---
if st.session_state.upload_clicked:
    upload_file = st.file_uploader("Upload your .mp3/.m4a/.txt/.vtt file", type=["mp3", "m4a", "vtt", "txt"])

    if st.button("📤 Upload"):  #Page resets when we click this button
        if upload_file is None:
            st.error("No file selected.")
        else:
            upload_dir = "recordings"   #Create a directory and upload the file for processing
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, upload_file.name)  #Set file path

            with open(file_path, "wb") as f:
                f.write(upload_file.read())

            st.success(f"✅ File successfully uploaded and ready for transcription")
            st.audio(file_path, format="audio/m4a") #Display an audio player for the uploaded file
            st.session_state["audio_path"] = file_path  # Save path for Whisper
            st.session_state["upload_file_name"] = upload_file.name

# --- Fetch Recordings from Zoom API ---
if "access_token" in st.session_state and not st.session_state.upload_clicked:
    if st.button("Fetch My Recordings"):
        if zoom_token_check():
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

#Transcription using OpenAI Whisper
if "audio_path" in st.session_state and os.path.exists(st.session_state["audio_path"]):
    from backend.transcribe_whisper import transcribe_audio
    file_path = st.session_state.get("audio_path", None)
    if st.button("📝 Transcribe"):
        if not file_path or not os.path.exists(file_path):
            st.error("⚠️ Invalid file path. Please re-upload the file!")
            st.write("File path",file_path)
        else:
            with st.spinner("Transcribing with Whisper..."):
                try:
                    transcript_text = transcribe_audio(file_path)
                    st.success("📝 Transcription complete!")
                    #st.text_area("Transcript", transcript_text, height=300)
                    st.session_state["transcript_text"] = transcript_text
                    
                    #Save transcript to a text file
                    transcript_file_path = f"outputs/{st.session_state['upload_file_name']}_transcript.txt"
                    os.makedirs("outputs", exist_ok=True)
                    with open(transcript_file_path, "w", encoding="utf-8") as f:
                        f.write(transcript_text)
                    
                    #Sending the transcript text to GPT for summary and action items
                    from backend.summarize_gpt import summarize_actions
                    if "transcript_text" in st.session_state:
                        with st.spinner("📋 Generating Summary and Action Items"):
                            try:
                                summary_output = summarize_actions(transcript_text)
                                st.session_state["summary_output"] = summary_output
                            except RuntimeError as e:   #Exception when GPT-4 summarization fails
                                st.error(str(e))
                except RuntimeError as e:   #Exception when transcibe by whisper fails
                    st.error(str(e))

#Download transcript
if "transcript_text" in st.session_state:
    transcript_file_path = f"outputs/{st.session_state['upload_file_name']}_transcript.txt"
    if os.path.exists(transcript_file_path):
        with open(transcript_file_path, "rb") as f:
            st.download_button(
                label="📥 Download Transcript",
                data=f,
                file_name = f"{st.session_state['upload_file_name']}_transcript.txt",
                mime="text/plain"
            )

if "summary_output" in st.session_state:
    st.text_area("Summary & Action Items", st.session_state["summary_output"], height=300)

#Sentiment Analysis of the Transcribed Text
if "transcript_text" in st.session_state and "summary_output" in st.session_state:
    from backend.sentiment_analysis import analyze_sentiment
    if st.button("🙂🙁 Get Meeting Mood"):
        with st.spinner("Analyzing meeting mood..."):
            try:
                sentiment_result = analyze_sentiment(st.session_state["transcript_text"])
                st.success("✅ Sentiment Analysis Complete")
                st.session_state["meeting_sentiment"] = sentiment_result[0]
                st.markdown(f"**Meeting Mood:** {sentiment_result[0]}")
            except RuntimeError as e:
                st.error("❌ Something went wrong")
                st.error(str(e))

#Testing Snippet: Sentiment Analysis by uploading a transcript text file. You can also enable this as a feature
# upload_transcribed_file = st.file_uploader("Upload your transcribed file", type=["txt"])
# if st.button("📤 Upload Transcribed File"):  #Page resets when we click this button
#         if upload_transcribed_file is None:
#             st.error("No file selected.")
#         else:
#             transcript_text = upload_transcribed_file.read().decode("utf-8")
#             st.session_state["transcript_text"] = transcript_text
# if "transcript_text" in st.session_state:
#     from backend.sentiment_analysis import analyze_sentiment
#     if st.button("🙂🙁 Get Meeting Mood"):
#         with st.spinner("Analyzing meeting mood..."):
#             try:
#                 sentiment_result = analyze_sentiment(st.session_state["transcript_text"])
#                 st.success("✅ Seniment Analysis Complete")
#                 st.markdown(f"**Meeting Mood:** {sentiment_result[0]}")
#             except RuntimeError as e:
#                 st.error("Something went wrong")
#                 st.error(str(e))

#Suggestions for manager based on the meeting seniment detected
if "transcript_text" in st.session_state and "meeting_sentiment" in st.session_state:
    if st.button("Manager Suggestions"):
        with st.spinner("Generating Suggestions..."):
            try:
                from backend.summarize_gpt import generate_suggestions
                suggestions = generate_suggestions(st.session_state["transcript_text"], st.session_state["meeting_sentiment"])
                st.text_area("Suggestions:", suggestions, height=300)
            except RuntimeError as e:
                st.error("❌ Something went wrong")
                st.error(str(e))