import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


# ─────────────────────────────────────────────────────────────────────────────
# summarize_actions()
# Purpose: Extract a short meeting summary and action items from transcript text
# Parameters:
#   - transcript (str): Full meeting transcript
# Returns:
#   - str: Combined summary and action items in readable format
# ─────────────────────────────────────────────────────────────────────────────
def summarize_actions(transcript:str) -> str:   #transcript:str is a type hint, indicating that transcript will be of type hint | -> str indicates the return type will be a string
    #A formatted string literal supporting multiple lines. \"\"\" indicates to the model that it is the start of the transcript
    prompt = f"""   
    You are an expert office meeting assistant. Given the transcript of a meeting, extract:
    1. A short meeting summary.
    2. A list of action items.

    Transcript:
    \"\"\"
    {transcript}
    \"\"\"
    Return both the summary and the action items clearly formatted.
    """ 
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system", "content":"You are an efficient and clear AI work assistant."},   #Sets assistant behavior
                {"role":"user","content":prompt}                                                    #Sets task for prompt
            ],
            temperature = 0.3   #Controls randomness of model (lower = focused, higher = more creative) | Since we need data from the existing transcription and no extra creativity is needed, we are keeping this value low
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Something went wrong {str(e)}"


# ─────────────────────────────────────────────────────────────────────────────
# generate_suggestions()
# Purpose: Suggest team management tips based on sentiment and meeting content
# Parameters:
#   - transcript_text (str): Full meeting transcript
#   - sentiment (str): Detected overall sentiment (e.g., Positive, Neutral, Negative)
# Returns:
#   - str: Actionable, concise suggestions for team managers
# ─────────────────────────────────────────────────────────────────────────────
def generate_suggestions(transcript_text:str, sentiment:str) -> str:
    prompt = f"""
    You are an expert HR assistant. Given the following meeting transcript and its detected sentiment, generate:

    - A **one-line summary** describing the overall situation and emotional tone of the conversation.
    - Then provide **2–3 short, practical suggestions** that the team manager can implement quickly. Each suggestion should be about 1–2 lines and clearly actionable.

    Focus on clarity, helpfulness, and brevity.

    Transcript:
    \"\"\"
    {transcript_text}
    \"\"\"

    Detected Sentiment:
    \"\"\"
    {sentiment}
    \"\"\"

    Return the output in this format:
    Summary: <your one-line summary here>

    Suggestions:
    - <suggestion 1>
    - <suggestion 2>
    - <suggestion 3>
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system","content":"You are an efficient and clear work assistant."},
                {"role":"user","content":prompt}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Somthing went wrong {str(e)}"
