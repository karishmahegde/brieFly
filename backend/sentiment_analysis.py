from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os
import torch
torch.classes.__path__ = []     #manually sets the __path__ attribute so Python doesn’t try to look for submodules inside torch.classes
import numpy as np
import emoji
import re

#Disable parallel processing in Hugging Face's tokenizer library to avoid warnings or potential deadlocks when using multiprocessing (e.g. in Streamlit)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ─────────────────────────────────────────────────────────────────────────────
# AutoTokenizer:
# - Converts raw human-readable text into model-readable inputs (tokens).
# - Automatically selects the appropriate tokenizer based on the model name.
# - Useful when working with different model architectures like BERT, RoBERTa, or GPT,
#   each of which uses a different tokenization strategy.
# - Looks for the 'config.json' file in the model's repository to determine the correct tokenizer.

# AutoModelForSequenceClassification:
# - Automatically loads a pre-trained transformer model configured for sequence classification tasks.
# - Includes both the model architecture and its trained weights.
# - Commonly used for tasks like sentiment analysis, intent detection, and topic classification.

# PyTorch
# - The twitter-roberta-base-sentiment model is based on PyTorch, hence we import this library

# emoji
# - Cleans/removes emojis from text before feeding it into the model for tokenization

# re
# - To work with regular expressions
# - For this code, we will filter URLs before feeding text to the model

#twitter-roberta-base-sentiment
# - The model used for sentiment analysis is the Hugging Face twitter-roberta-base-sentiment
# - This is a roBERTa-base model trained on ~58M tweets and finetuned for sentiment analysis with the TweetEval benchmark. 
# - Labels: 0 -> Negative; 1 -> Neutral; 2 -> Positive
# - https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment
# ─────────────────────────────────────────────────────────────────────────────

# --- Load Pretrained Model & Tokenizer ---
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, force_download=True)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

# --- Preprocessing Text ---
def preprocess(text):
    text = emoji.replace_emoji(text, replace='')    #remove emojis in transcript
    text = re.sub(r"http\S+","",text)   #remove URLs | substitute the pattern match i.e. URLs with empty 
    return text.strip()

# --- Sentiment Analysis Model ---
def analyze_sentiment(text):
    """
    Returns the sentiment label and confidence score for the given text.
    """
    #Preprocess text to remove URLs and Emojis
    text = preprocess(text) 
    #Return_tensors="pt" means to return the tokens in PyTorch tensor format | truncation=True tells the tokenizer to truncate the text if it's too long for the model (max = 512 tokens)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)


    with torch.no_grad(): #Since we are not training the model, no_grad is used to stop PyTorch from tracking gradients
        #Pass the tokenized input to the RoBERTa model
        # - **input unpacks the dictionary into keyword arguments (input_ids, attention_mask)
        # - .logits gives the raw scores (logits) for each class from the output layer
        logits = model(**inputs).logits 

    probs = torch.nn.functional.softmax(logits, dim=-1) #Apply softmax to convert logits into probabilities 
    predicted_class = torch.argmax(probs).item()    #Finds the index of the class with the highest probability, which corresponds to the sentiment the model has identfied
    sentiment_labels = ['Negative', 'Neutral', 'Positive']
    sentiment = sentiment_labels[predicted_class]
    confidence = probs[0][predicted_class].item()   #Confidence score of the predicted class
    return sentiment, round(confidence, 3)  #Return the sentiment and the confidence score