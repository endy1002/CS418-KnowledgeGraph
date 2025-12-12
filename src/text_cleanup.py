import google.generativeai as genai

API_KEY = "AIzaSyA22Rd8yKKTfEc2ljPK-1oi5wvrGvX3LOg"
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-flash-latest")

def cleanup_text(dirty_text):
    prompt = f"""
    I have some text extracted via OCR that contains noise and formatting errors. 
    Please correct the text below into clean Vietnamese.
    Don'r remove the section title indices.
    For bullet list, at the beginning each of those lists can you add a <begin items> and at its end a <end items>?
    The context is traditional medicinal weights.

    Text to clean:
    {dirty_text}
    """

    response = model.generate_content(prompt)
    print(response.text)
    dirty_text = response.text