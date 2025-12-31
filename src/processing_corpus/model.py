import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import os
import sys

def preprocess_image(image_path):
    try:
        img = Image.open(image_path)
        # Convert to grayscale
        img = img.convert('L')

        # Upscale the image (2x) to help with small details/accents
        width, height = img.size
        new_size = (width * 2, height * 2)
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        
        # Apply thresholding
        # Using a slightly higher threshold to catch lighter text, 
        # or use a simple binary threshold if lighting is consistent enough.
        # For now, let's try a standard threshold but on the enhanced image.
        threshold = 180 
        img = img.point(lambda p: p > threshold and 255)
        
        return img
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def main():
    filename = 'image.png'
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    path = os.path.dirname(__file__)
    image_path = os.path.join(os.path.dirname(path), 'assets', filename)

    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")  
        return

    try:
        print(f"Processing {filename}...")
        img = preprocess_image(image_path)
        
        if img:
            text = pytesseract.image_to_string(img, lang='vie')
            
            print("OCR Result:")
            print("-" * 20)
            print(text)
            print("-" * 20)
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
