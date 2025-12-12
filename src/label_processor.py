import cv2
import numpy as np
import pytesseract
import re
import os
import math
import numpy as np
import cv2

def smart_crop(img, box, padding=5):
    """
    Crops an image safely by:
    1. Flooring the top-left (round down).
    2. Ceiling the bottom-right (round up).
    3. Adding padding to ensure edges aren't cut off.
    4. clamping to image boundaries so it doesn't crash.
    """
    h, w, _ = img.shape
    
    # Unpack float coordinates
    x1_float, y1_float, x2_float, y2_float = box
    
    # "Round Outwards" Strategy
    # x1/y1: floor() to move left/up (capture more context)
    # x2/y2: ceil() to move right/down (capture more context)
    x1 = math.floor(x1_float)
    y1 = math.floor(y1_float)
    x2 = math.ceil(x2_float)
    y2 = math.ceil(y2_float)
    
    # Add Padding (The most important fix for "tight" boxes)
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(w, x2 + padding)
    y2 = min(h, y2 + padding)
    
    return img[y1:y2, x1:x2]

# 1. DEFINE LABEL GROUPS
# Labels that represent visual content we want to save as images
IMAGE_LABELS = ['figure', 'chart']

# Labels that represent text we want to save separately (not as body text)
# We will OCR these specific boxes individually.
META_TEXT_LABELS = ['figure_title', 'figure_caption', 'caption', 'table_caption']

# Labels we just want to delete (mask) so they don't pollute the body text
# We include the groups above in this list too, plus headers/footers.
ALL_MASK_LABELS = IMAGE_LABELS + META_TEXT_LABELS + ['table', 'equation', 'formula', 'header', 'footer', 'page_number', 'reference']

def process_region_layout(img, det_boxes, lang='vie'):
    """
    1. Extracts images (Figures/Charts).
    2. Extracts metadata text (Captions/Titles) separately.
    3. Returns a 'clean' image with ALL of the above whited out.
    """
    img_h, img_w, _ = img.shape
    img_masked = img.copy()
    
    extracted_items = []

    for i, box in enumerate(det_boxes):
        label = box.get('label', 'text')
        coords = [int(c) for c in box['coordinate']]
        x1, y1, x2, y2 = coords
        print("Start anti-label extractions.")
        roi = img[y1:y2, x1:x2]
        
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test.png")

        cv2.imwrite(base_path, roi)

        input()

        # --- A. EXTRACTION LOGIC ---
        
        # # Case 1: It is an Image (Figure/Chart) -> Crop and Save Image
        # if label in IMAGE_LABELS:
        #     # Optional: Add small padding for better visual crop
        #     pad = 5
        #     cx1, cy1 = max(0, x1 - pad), max(0, y1 - pad)
        #     cx2, cy2 = min(img_w, x2 + pad), min(img_h, y2 + pad)
            
        #     crop_img = img[cy1:cy2, cx1:cx2]
            
        #     extracted_items.append({
        #         'type': 'image',
        #         'label': label,
        #         'content': crop_img, # This is a numpy array (image)
        #         'box': coords
        #     })

        # Case 2: It is a Label/Caption -> OCR it specifically and Save Text
        if label in META_TEXT_LABELS:
            # Crop the text box
            roi = img[y1:y2, x1:x2]
            
            # base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test.png")

            # cv2.imwrite(base_path, roi)

            # input()

            # Run OCR with 'Single Block' config (--psm 6)
            # This is much more accurate for captions than running page-level OCR
            if roi.size > 0:
                caption_text = pytesseract.image_to_string(roi, lang=lang, config='--psm 6')
                print(caption_text)
                caption_text = re.sub(r'\n', ' ', caption_text) # Remove newlines
                
                extracted_items.append({
                    'type': 'text_metadata',
                    'label': label,
                    'content': caption_text, # This is a string
                    'box': coords
                })

        # --- B. MASKING LOGIC ---
        # If it falls into ANY category we want to exclude from the main body...
        # if label in ALL_MASK_LABELS:
            # Draw a solid white rectangle over it
            cv2.rectangle(img_masked, (x1, y1), (x2, y2), (255, 255, 255), -1)

    return extracted_items, img_masked