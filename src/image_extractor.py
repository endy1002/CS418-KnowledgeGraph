import os
import cv2
from paddleocr import PPStructureV3

# 1. Initialize the Layout Analysis Engine
# table=False: We focus on general layout (text vs image), not complex table reconstruction
# ocr=True: We want it to read the text inside the text blocks
# lang='vi': CRITICAL for your document (Vietnamese)
engine = PPStructureV3(lang='vi')
print("Model loaded successfully.")

parent_path = os.path.dirname(os.path.abspath(__file__))
# img_path = os.path.join(os.path.dirname(os.path.abspath(parent_path)), "assets", "image.png")
img_path = os.path.join(os.path.dirname(os.path.abspath(parent_path)), "assets", "test", "4.png")
img = cv2.imread(img_path)

# 2. Run the analysis
# This returns a list of regions found (Titles, Text blocks, Figures)
result = engine.predict(img)

print(type(result))

# 3. Process the results manually (to see how it works)
print(f"Found {len(result)} regions.")

def process(region: dict):
    output_dir = os.path.join(os.path.dirname(os.path.abspath(parent_path)), "results", "image_test")
    os.makedirs(output_dir, exist_ok=True)
    # --- 1. HANDLE TEXT (from parsing_res_list) ---
    print("--- Text Extraction ---")
    structure_list = region.get('parsing_res_list', [])

    for i, block in enumerate(structure_list):
        label = block.label
        text = block.content
        
        # We only care about text-containing blocks
        if label in ['text', 'header', 'figure_title', 'section_header']:
            print(f"[{label.upper()}]: {text}")

    # --- 2. HANDLE IMAGES (from imgs_in_doc) ---
    print("\n--- Image Extraction ---")
    images_list = region.get('imgs_in_doc', [])

    for i, img_item in enumerate(images_list):
        # The 'img' key contains a PIL Image object
        pil_image = img_item['img']
        
        if pil_image:
            save_path = os.path.join(output_dir, f"extracted_figure_{i}.jpg")
            
            # PIL uses .save(), not cv2.imwrite
            pil_image.save(save_path)
            print(f"Saved image to: {save_path}")
    
    # --- 3. HANDLE TABLES ---
    print("\n--- Table Extraction ---")
    table_list = region['table_res_list']
    print(table_list)

    # --- 4. HANDLE CHARTS ---
    print("\n--- Charts Extraction ---")
    chart_list = region['chart_res_list']
    print(chart_list)

    # --- 5. HANDLE FORMULAS ---
    print("\n--- Formulas Extraction ---")
    formula_list = region['formula_res_list']
    print(formula_list)

    pass

for i, region in enumerate(result):
    # 'type' is usually capitalized in V3 (e.g., 'Figure', 'Text', 'Table')
    # We use .lower() to make it case-insensitive for your checks
    print(f"Processing for region {i}...")
    process(region)
    print(f"Processing complete.")

# Remarks:
# - tables and images are extracted normally, not too much of a surprise
# - chart extraction is numb, check it out on image 3.png, for some reason
# - idk if it is neat or problematic but formulas are automatically classified as images by PPOCR
# - it still sucks with Vietnamese