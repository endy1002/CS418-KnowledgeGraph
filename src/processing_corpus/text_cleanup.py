import os

import google.generativeai as genai
from dotenv import load_dotenv


def configure_model():
    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def cleanup_text(dirty_text):
    model = genai.GenerativeModel("gemini-flash-latest")
    prompt = f"""
    I have some text extracted via OCR that contains noise and formatting errors.
    The text is related to traditional Eastern medicine.

    - The text will be provided as an array of JSON strings.
    - Correct each element individually and return **only** the
    corresponding JSON array. Do not wrap the array in Markdown or any other form of formatting.
    - For each element in the array, if the provided element is blank, then the corresponding output element should also be blank.
    - The returned JSON array must have the same number of elements as the provided JSON array.

    - Do not make up new content if there's too little text!
    - Do not change words into synonyms, only correct spelling and punctuation errors.
    - If the character of "_" is not grammatically correct at a position, try to replace it with character "...".
    - Do not remove section title indices.
    - For bullet lists, add a <begin items> at the start and a <end items> at the end. Do not add Markdown or HTML
    formatting for anything else.

    Text to clean:
    {dirty_text}
    """

    response = model.generate_content(prompt)
    return response
