import google.generativeai as genai
import os
from dotenv import load_dotenv


def configure_model():
    load_dotenv()
    genai.configure(api_key=os.getenv("API_KEY"))
    
def cleanup_text(dirty_text):
    model = genai.GenerativeModel("gemini-flash-latest")
    prompt = f"""
    I have some text extracted via OCR that contains noise and formatting errors. 
    Please correct the text below into clean Vietnamese, within the context.
    Please don't change any word into possible synonyms, just correct the text only.
    Please also fix the punctuation if possible.
    If the character of "_" is not grammatically correct at a position, try to replace it with character "...".
    Print it like printing plain texts, no symbols for bold or italic.
    Don't remove the section title indices.
    For bullet list, at the beginning each of those lists can you add a <begin items> and at its end a <end items>?
    The context is traditional medicinal weights.

    Text to clean:
    {dirty_text}
    """

    response = model.generate_content(prompt)
    return response.text