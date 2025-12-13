import json
import os

from dotenv import load_dotenv
from google import genai


def configure_model():
    pass


load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def cleanup_text(dirty_text: list[str]):
    prompt = f"""
    I have some text extracted via OCR that contains noise and formatting errors.
    The text is related to traditional Eastern medicine.

    - The text will be provided as an array of JSON strings.
    - Correct each element individually and return **only** the
    corresponding JSON array. Do not wrap the array in Markdown or any other form of formatting.
    - For each element in the array, if the provided element is blank, then the corresponding output element should also be blank.
    - Respect existing linebreaks and preserve them in the output.

    - Do not make up new content if there's too little text!
    - Do not change words into synonyms, only correct spelling and punctuation errors.
    - If the character of "_" is not grammatically correct at a position, try to replace it with character "...".
    - Do not remove section title indices.
    - For bullet lists, add a <begin items> at the start and a <end items> at the end. Do not add Markdown or HTML
    formatting for anything else.

    Text to clean:
    {json.dumps(dirty_text)}
    """

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": len(dirty_text),
                "maxItems": len(dirty_text),
            },
        },
    )

    return response
