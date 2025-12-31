import os
import re
import unicodedata
import json
from docx import Document
from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
import table_processing

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

def iter_block_items(parent):
    """
    Yields Table or Paragraph objects in order.
    """
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

def is_list_item_xml(paragraph):
    """
    Check if it is a list using Word's internal XML (Best for formatted docs).
    """
    if paragraph._p.pPr is not None and paragraph._p.pPr.numPr is not None:
        return True
    return False

def is_list_item_regex(text):
    """
    Check if it looks like a list using Regex (Fallback for raw text).
    Matches: 
      - Numbers: "1.", "1)", "01."
      - Letters: "a.", "b)"
      - Symbols: "•", "-", "*", "°", "▪", "+"
    """
    # 1. Define the set of bullet symbols you want to support
    bullet_symbols = r"•\-\*°▪+" 
    
    # 2. Construct the regex
    # ^        : Start of string
    # [\s\t]* : Optional whitespace indentation
    # (?: ... ): Non-capturing group for the alternatives
    # \s+      : Must have whitespace after the bullet (e.g. "° " not "°C")
    pattern = rf'^[\s\t]*(?:\d{{1,2}}[\.\)]|[a-z][\.\)]|[{bullet_symbols}])\s+'
    
    return re.match(pattern, text) is not None


def clean_text(text):
    text = unicodedata.normalize('NFC', text)
    # Note: We do NOT remove newlines here because we want to detect block boundaries
    return text.strip()

def process_document(file_path):
    doc = Document(file_path)
    
    all_sections = []
    current_section = {"id": 1, "sentences": []}
    
    # --- NEW STATE VARIABLE: THE BUFFER ---
    # Holds text that is "waiting" to see if the next line continues it.
    pending_text = ""
    
    # Context memory for lists/tables
    last_lead_in = "" 
    list_counter = 0
    in_list_block = False

    print(f"--- Processing {file_path} ---")

    for block in iter_block_items(doc):
        
        # ==================================================
        # CASE 1: TABLE (Always breaks the flow)
        # ==================================================
        if isinstance(block, Table):
            # 1. Flush any pending text first (Table means previous sent is done)
            if pending_text:
                current_section["sentences"].append(pending_text)
                last_lead_in = pending_text # Use it as context
                pending_text = ""
            
            # 2. Process Table
            table_sents = table_processing.process_table_smart(block, context=last_lead_in)
            current_section["sentences"].extend(table_sents)
            
            # Reset context
            last_lead_in = "Bảng dữ liệu" 
            in_list_block = False
            continue

        # ==================================================
        # CASE 2: PARAGRAPH (Text or List)
        # ==================================================
        if isinstance(block, Paragraph):
            raw_text = clean_text(block.text)
            if not raw_text: continue

            # --- A. CHECK FOR SECTION BREAK ---
            if "</break>" in raw_text:
                # Flush pending text to the OLD section
                if pending_text:
                    current_section["sentences"].append(pending_text)
                    pending_text = ""

                # Handle the split
                parts = raw_text.split("</break>")
                if parts[0].strip():
                    current_section["sentences"].append(parts[0].strip())
                
                # Save & Reset
                if current_section["sentences"]:
                    all_sections.append(current_section)
                
                current_section = {"id": current_section["id"] + 1, "sentences": []}
                last_lead_in = ""
                
                # Update current text to the new section's part
                raw_text = parts[1].strip()
                if not raw_text: continue
            
            # --- B. CHECK FOR LIST ITEM ---
            is_xml_list = is_list_item_xml(block)
            is_regex_list = is_list_item_regex(raw_text)
            
            if is_xml_list or is_regex_list:
                # 1. FLUSH PREVIOUS BUFFER
                if pending_text:
                    current_section["sentences"].append(pending_text)
                    
                    # --- BUG FIX HERE ---
                    # Only update context if we were NOT already in a list.
                    # If we are already in a list, 'pending_text' is just the previous sibling (Item 1).
                    # We DON'T want Item 2 to inherit Item 1 as its context.
                    # We want it to keep the ORIGINAL context (the Title).
                    if not in_list_block:
                        last_lead_in = pending_text 
                    
                    pending_text = ""

                # 2. Handle List Logic
                if not in_list_block:
                    list_counter = 1
                else:
                    list_counter += 1
                
                clean_content = raw_text
                if is_regex_list:
                    # Remove "1." or "-" marker
                    clean_content = re.sub(r'^[\s\t]*(?:\d{1,2}[\.\)]|[a-z][\.\)]|[•\-\*°▪])\s+', '', raw_text)
                
                # 3. SET TO BUFFER
                # Uses 'last_lead_in' which is preserved from BEFORE the list started
                full_sent = f"{last_lead_in} Bước {list_counter}: {clean_content}"
                pending_text = full_sent
                
                in_list_block = True
                
            # --- C. NORMAL TEXT (MERGE LOGIC) ---
            else:
                first_char = raw_text[0]
                starts_lowercase = first_char.islower()
                
                # CASE C1: MERGE (Continuation of previous block)
                if starts_lowercase and pending_text:
                    pending_text += " " + raw_text
                    
                    # --- CRITICAL FIX ---
                    # Do NOT reset 'in_list_block' or 'list_counter' here.
                    # We are still conceptually inside the list item (just reading line 2 of it).
                    # --------------------

                # CASE C2: NEW SENTENCE
                else:
                    # 1. Save the previous buffer
                    if pending_text:
                        current_section["sentences"].append(pending_text)
                        
                        # Only update context if we are NOT currently in a list 
                        # (prevents a list item from becoming the context for the next normal sentence)
                        if not in_list_block:
                            last_lead_in = pending_text
                        
                    # 2. Start new buffer
                    pending_text = raw_text
                    
                    # 3. NOW we reset state, because we truly broke the list flow
                    in_list_block = False
                    list_counter = 0
                
    # End of Loop: Flush whatever is left in the buffer
    if pending_text:
        current_section["sentences"].append(pending_text)
    
    if current_section["sentences"]:
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
            record = {
                "doc_id": filename,
                "section_id": sec["id"],
                "paragraphs": sec["sentences"],
                # Add any extra metadata here
            }
            
            # Write one line per section
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Saved {len(sections)} sections to {output_path}")

if __name__ == "__main__":
    corpus_directory = "corpus"
    extension = ".docx"
    files = locate_corpus_files(corpus_directory, extension)
    for f in files:
        sections = process_document(f)
        save_to_jsonl(sections, os.path.basename(f))