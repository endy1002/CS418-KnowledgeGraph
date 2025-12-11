import os
import cv2
import pytesseract
from PIL import Image
from image_extractor import engine, process
import text_cleanup

def preprocess_image(img_cv2):
    try:
        # Check if valid image
        if img_cv2 is None:
            return None
            
        # Convert to grayscale
        gray = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB)

        # Upscale (2x) to help with small details/accents
        # Linear interpolation is usually good enough and faster, or Cubic/Lanczos4 for quality
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # Adaptive Thresholding
        # GaussianC is better for varying lighting than MeanC.
        """
        thresh = cv2.adaptiveThreshold(
            gray, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            31, # Block Size (must be odd)
            15  # Constant subtracted from mean (tweak if too black or too white)
        )
        """
        # Convert back to PIL Image for compatibility with pytesseract
        return Image.fromarray(gray)
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def process_image(image_path, base_output_dir):
    filename = os.path.splitext(os.path.basename(image_path))[0]
    output_dir = os.path.join(base_output_dir, filename)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Processing: {image_path}")
    print(f"Output directory: {output_dir}")

    try:
        # Load Main Image
        img_original = cv2.imread(image_path)
        if img_original is None:
            print(f"Error: Could not read {image_path}")
            return
        
        height, width, *_ = img_original.shape
        max_size = max(height, width)
        if max_size >= 1920:
            scale = 1920.0/max_size
            img_original = cv2.resize(img_original, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        # Prepare directory for extracted images
        extracted_images_dir = os.path.join(output_dir, "extracted_images")
        os.makedirs(extracted_images_dir, exist_ok=True)

        # --- 1. Layout Analysis & Extraction ---
        print("--- Running Layout Analysis ---")
        result = engine.predict(img_original)
        print(f"Found {len(result)} regions.")
        
        # Create a copy for masking (OCR Image)
        img_for_ocr = img_original.copy()
        img_h, img_w, _ = img_original.shape       
        for region_idx, region in enumerate(result):
             # 1. Save Original Sub-Images (PDF embedded images)
            images_list = region.get('imgs_in_doc', [])
            for i, img_item in enumerate(images_list):
                 pil_image = img_item['img']
                 if pil_image:
                     save_path = os.path.join(extracted_images_dir, f"region_{region_idx}_img_{i}.jpg")
                     pil_image.save(save_path)
                     print(f"Saved extract: {save_path}")

            # 2. Handle Detection Boxes (Masking & Saving)
            # We iterate layout_det_res to find charts, tables, figures, formulas etc.
            det_boxes = region.get('layout_det_res', {}).get('boxes', [])
            
            for i, box in enumerate(det_boxes):
                label = box.get('label')
                x1, y1, x2, y2 = [int(c) for c in box['coordinate']]
                
                # Check labels to mask
                # PPStructure labels: 'text', 'title', 'figure', 'figure_caption', 'table', 'table_caption', 'header', 'footer', 'reference', 'equation'
                # We want to mask: 'figure', 'table', 'equation' (formula), 'chart'
                
                if label in ['figure', 'table', 'equation', 'chart', 'formula']:
                    print(f"Found {label}: Masking region [{x1}:{x2}, {y1}:{y2}]")
                    
                    # A. Save the element
                    # Add padding for nicer cut
                    pad = 10
                    cx1, cy1 = max(0, x1 - pad), max(0, y1 - pad)
                    cx2, cy2 = min(img_w, x2 + pad), min(img_h, y2 + pad)
                    
                    element_crop = img_original[cy1:cy2, cx1:cx2]
                    save_path = os.path.join(extracted_images_dir, f"region_{region_idx}_{label}_{i}.jpg")
                    cv2.imwrite(save_path, element_crop)

                    # B. Mask the element in the OCR image (Fill with WHITE)
                    # We use exact coordinates for masking to ensure we cover it
                    cv2.rectangle(img_for_ocr, (x1, y1), (x2, y2), (255, 255, 255), -1)

            # 3. Handle Tables (HTML) - just saving, masking already handled by box above usually
            table_list = region.get('table_res_list', [])
            for i, table in enumerate(table_list):
                html = table.get('pred_html')
                if html:
                    save_path = os.path.join(extracted_images_dir, f"region_{region_idx}_table_{i}.html")
                    with open(save_path, "w", encoding='utf-8') as f:
                        f.write(html)

        # --- 2. OCR (Text Extraction on Masked Image) ---
        print("--- Running OCR (Text) ---")
        # Preprocess the MASKED image
        processed_img_pil = preprocess_image(img_for_ocr)
        
        if processed_img_pil:
            # We use pytesseract on the processed PIL image
            text = pytesseract.image_to_string(processed_img_pil, lang='vie')
            text = text_cleanup.cleanup_text(text)
            text_file_path = os.path.join(output_dir, f"{filename}.txt")
            with open(text_file_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Saved cleaned text to: {text_file_path}")
        else:
            print("Failed to preprocess masked image.")

    except Exception as e:
         print(f"Error during processing: {e}")

def main():
    text_cleanup.configure_model()

    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Project root
    # User said: test with any image in /assets/testing/
    # If assets/testing exists, use it. Else use assets/test.
    
    testing_dir = os.path.join(base_dir, "assets", "test2")
    
    results_dir = os.path.join(base_dir, "results")
    
    if not os.path.exists(testing_dir):
        print(f"Error: Testing directory not found at {testing_dir}")
        return

    files = [f for f in os.listdir(testing_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not files:
        print(f"No images found in {testing_dir}")
        return

    print(f"Found {len(files)} images to process.")
    for f in files:
        img_path = os.path.join(testing_dir, f)
        process_image(img_path, results_dir)

if __name__ == "__main__":
    main()
