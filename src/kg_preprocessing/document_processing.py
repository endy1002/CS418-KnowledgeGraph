import os
import re
import unicodedata
import json
from dotenv import load_dotenv
from docx import Document
from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from underthesea import sent_tokenize
import py_vncorenlp
import table_processing

load_dotenv()
os.environ["JAVA_HOME"] = os.getenv("JAVA_HOME") # Set JAVA_HOME for py_vncorenlp, use your actual path that supports Java 8+, x64.
rdrsegmenter = py_vncorenlp.VnCoreNLP(annotators=["wseg"], save_dir=os.getcwd())

def locate_corpus_files(corpus_dir, file_extension):
    """
    Locate all files with the given extension in the specified corpus directory.

    Args:
        corpus_dir (str): The directory to search for corpus files.
        file_extension (str): The file extension to look for (e.g., '.txt').

    Returns:
        list: A list of file paths matching the specified extension.
    """
    import os

    matched_files = []
    for root, dirs, files in os.walk(corpus_dir):
        for file in files:
            if file.endswith(file_extension):
                matched_files.append(os.path.join(root, file))
    
    return matched_files

# ==========================================
# 1. HELPERS & DETECTORS
# ==========================================

def iter_block_items(parent):
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("Invalid parent")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def has_image(paragraph):
    """Checks if paragraph contains an image (drawing or shape)."""
    return bool(paragraph._p.xpath('.//w:drawing') or paragraph._p.xpath('.//w:pict'))

def is_list_item_xml(paragraph):
    return paragraph._p.pPr is not None and paragraph._p.pPr.numPr is not None

def is_list_item_regex(text):
    # Removed '-' to prevent confusion with hyphens, added common symbols
    bullet_symbols = r"•\*°▪+" 
    pattern = rf'^[\s\t]*(?:\d{{1,2}}[\.\)]|[a-z][\.\)]|[{bullet_symbols}])\s+'
    return re.match(pattern, text) is not None

def clean_text(text):
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'([a-zA-Zà-ỹÀ-Ỹ,;-])\n([a-zà-ỹ])', r'\1 \2', text)
    return text.strip()

# ==========================================
# 2. TABLE PARSERS (Your Adaptive Strategy)
# ==========================================
# (Keep the smart_process_table functions we defined previously here)
# For brevity, I will call a placeholder. Ensure you include the "Transposed" logic here.
def smart_process_table(table, context):
    # ... [Insert the Smart Router logic from previous steps] ...
    # For now, returning basic rows to keep script runnable
    return [f"{context}: Table Row Data"] 

# ==========================================
# 3. MAIN PIPELINE
# ==========================================

def process_document(file_path):
    doc = Document(file_path)
    
    all_sections = []
    current_section = {"id": 1, "sentences": [], "figures": []}
    
    # --- STATE VARIABLES ---
    pending_text = ""       # For merging lowercase sentences
    in_list_block = False   # To track list item siblings
    last_lead_in = ""       # The "Title" context for lists
    expecting_caption = False # The "Trap" for the next line
    
    print(f"--- Processing {file_path} ---")

    for block in iter_block_items(doc):
        
        # ------------------------------------
        # A. HANDLE TABLES
        # ------------------------------------
        if isinstance(block, Table):
            expecting_caption = False # Table breaks image-caption flow
            
            # Flush pending text (previous sentence is done)
            if pending_text:
                current_section["sentences"].append(pending_text)
                last_lead_in = pending_text 
                pending_text = ""
            
            table_sents = table_processing.process_table_smart(block, context=last_lead_in)
            current_section["sentences"].extend(table_sents)
            
            last_lead_in = "Bảng dữ liệu"
            in_list_block = False
            continue

        # ------------------------------------
        # B. HANDLE PARAGRAPHS
        # ------------------------------------
        if isinstance(block, Paragraph):
            
            # 1. IMAGE DETECTION
            if has_image(block):
                # If we were already expecting a caption (Image -> Image), 
                # the previous image had NONE.
                expecting_caption = True
                
                # Check for inline text (rare caption inside image line)
                raw_text = clean_text(block.text)
                if raw_text:
                    current_section["figures"].append({
                        "caption": raw_text,
                        "location": len(current_section["sentences"])
                    })
                    expecting_caption = False # Found it inline
                continue

            # 2. TEXT EXTRACTION
            raw_text = clean_text(block.text)
            if not raw_text: continue

            # 3. CAPTION TRAP (Strict Next-Line Rule)
            if expecting_caption:
                # Check strictly for Stop Signals
                if "</break>" in raw_text:
                    # Case: Image -> Break (No Caption)
                    expecting_caption = False 
                    # Fall through to process the break below...
                else:
                    current_section["figures"].append({
                        "caption": raw_text,
                        "location": len(current_section["sentences"])
                    })
                    expecting_caption = False 
                    continue # Done. Do not add to body text.

            # 4. BREAK DETECTION
            if "</break>" in raw_text:
                # Flush pending text
                if pending_text:
                    current_section["sentences"].append(pending_text)
                    pending_text = ""
                
                parts = raw_text.split("</break>")
                if parts[0].strip():
                    current_section["sentences"].append(parts[0].strip())

                # Save Section
                if current_section["sentences"] or current_section["figures"]:
                    all_sections.append(current_section)
                
                # Start New Section
                current_section = {"id": current_section["id"] + 1, "sentences": [], "figures": []}
                last_lead_in = ""
                
                # Process remaining text (Start of new section)
                raw_text = parts[1].strip()
                if not raw_text: continue

            # 5. LIST DETECTION
            is_xml_list = is_list_item_xml(block)
            is_regex_list = is_list_item_regex(raw_text)
            
            if is_xml_list or is_regex_list:
                # Flush previous buffer
                if pending_text:
                    current_section["sentences"].append(pending_text)
                    # FIX: Only update context if we are NOT in a list
                    if not in_list_block:
                        last_lead_in = pending_text 
                    pending_text = ""

                # Handle List Logic
                if not in_list_block:
                    list_counter = 1
                else:
                    list_counter += 1
                
                clean_content = raw_text
                if is_regex_list:
                    clean_content = re.sub(r'^[\s\t]*(?:\d{1,2}[\.\)]|[a-z][\.\)]|[•\*°▪+])\s+', '', raw_text)
                
                # Set to buffer
                full_sent = f"{last_lead_in} Bước {list_counter}: {clean_content}"
                pending_text = full_sent
                in_list_block = True
            
            # 6. NORMAL TEXT (MERGE LOGIC)
            else:
                first_char = raw_text[0]
                starts_lowercase = first_char.islower()
                
                if starts_lowercase and pending_text:
                    # Merge into pending (list item or previous sentence)
                    pending_text += " " + raw_text
                    # CRITICAL FIX: Do NOT reset in_list_block here
                else:
                    # New distinct sentence
                    if pending_text:
                        current_section["sentences"].append(pending_text)
                        if not in_list_block:
                            last_lead_in = pending_text
                    
                    pending_text = raw_text
                    in_list_block = False # Reset state
                    list_counter = 0

    # End of Loop Cleanup
    if pending_text:
        current_section["sentences"].append(pending_text)
    if current_section["sentences"] or current_section["figures"]:
        all_sections.append(current_section)

    return all_sections

def save_to_jsonl(sections, filename, output_dir="results"):
    # 1. Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "corpus_master.jsonl")
    # 2. Open in 'Append' mode ('a')
    # This ensures you can process files one by one without overwriting previous work
    with open(output_path, 'a', encoding='utf-8') as f:
        for sec in sections:
            # Construct the final record
            record = []
            for i, paragraph in enumerate(sec["sentences"]):
                sec["sentences"][i] = sent_tokenize(paragraph)
                for j, sent in enumerate(sec["sentences"][i]):
                    original_sent = sent
                    sec["sentences"][i][j] = rdrsegmenter.word_segment(sent)
                    record.append({
                        "id": f"{filename}_sec{sec['id']}_para{i+1}_sent{j+1}",
                        "original_text": original_sent,
                        "segmented_text": sec["sentences"][i][j],
                        "tokens": sec["sentences"][i][j][0].split(" "),
                        "ner_tags": ["O"] * len(sec["sentences"][i][j][0].split(" ")),
                        "metadata": {
                            "type": "text",
                            "source_file": filename,
                            "section_id": sec["id"]
                        }
                    })
            for i, fig in enumerate(sec["figures"]):
                sec["figures"][i]["caption"] = sent_tokenize(fig["caption"])
                for j, sent in enumerate(sec["figures"][i]["caption"]):
                    original_sent = sent
                    sec["figures"][i]["caption"][j] = rdrsegmenter.word_segment(sent)
                    record.append({
                        "id": f"{filename}_sec{sec['id']}_fig{i+1}_sent{j+1}",
                        "original_text": original_sent,
                        "segmented_text": sec["figures"][i]["caption"][j][0],
                        "tokens": sec["figures"][i]["caption"][j][0].split(" "),
                        "ner_tags": ["O"] * len(sec["figures"][i]["caption"][j][0].split(" ")),
                        "metadata": {
                            "type": "figure_caption",
                            "source_file": filename,
                            "section_id": sec["id"],
                            "figure_location": fig["location"]
                        }
                    })
            # Write one line per section
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Saved {len(sections)} sections to {output_path}")

if __name__ == "__main__":
    corpus_directory = "corpus"
    extension = ".docx"
    files = locate_corpus_files(corpus_directory, extension)
    with open(os.path.join("results", "corpus_master.jsonl"), 'w') as log_file:
        log_file.write("")
    for f in files:
        sections = process_document(f)
        save_to_jsonl(sections, os.path.basename(f))