def process_table_smart(table, context):
    rows = table.rows
    if len(rows) < 2: return []
    
    # Normalize first cell text for checking
    first_cell_text = rows[0].cells[0].text.strip().lower()
    
    # --- COLLISION HANDLING: "Ngũ hành" ---
    if "ngũ hành" in first_cell_text:
        # Strategy: Count unique text values in Row 0 vs Row 1
        
        # Get text from all cells in Row 0
        row0_values = [c.text.strip() for c in rows[0].cells if c.text.strip()]
        unique_r0 = set(row0_values)
        
        # Get text from all cells in Row 1
        row1_values = [c.text.strip() for c in rows[1].cells if c.text.strip()]
        unique_r1 = set(row1_values)

        # LOGIC: 
        # If Row 0 has FEWER unique items than Row 1, it implies Merged Headers (Type 2).
        # (e.g. Row 0 has 2 items ["Ngũ hành", "Tự nhiên"], Row 1 has 6 items ["Hướng", "Mùa"...])
        if len(unique_r0) < len(unique_r1):
            return parse_grouped_header_table(table)
        
        # Otherwise, if Row 0 has many items (Mộc, Hỏa...), it is Transposed (Type 3).
        else:
            return parse_transposed_table(table)

    # --- OTHER TYPES ---
    
    # Check for Headless / Implicit (Type 4)
    # Heuristic: Check column 1 for date indicators like "năm" or "TCN"
    # and ensure it's NOT one of the complex tables above.
    if len(rows[0].cells) > 1:
        sample_cell = rows[0].cells[1].text.lower()
        if "năm" in sample_cell or "tcn" in sample_cell:
            return parse_headless_table(table, context)

    # Default to Standard (Type 1)
    return parse_standard_table(table, context)

# --- INDIVIDUAL PARSERS ---

def parse_standard_table(table, context):
    # Standard: Row 0 is Header, Col 0 is Entity
    headers = [c.text.strip() for c in table.rows[0].cells]
    sentences = []
    for row in table.rows[1:]:
        subject = row.cells[0].text.strip()
        for i in range(1, len(row.cells)):
            if i < len(headers):
                relation = headers[i]
                val = row.cells[i].text.strip()
                # Clean up newlines in cells
                val = val.replace('\n', ', ') 
                sentences.append(f"{context}: {headers[0]} {subject} có {relation} là {val}.")

    return sentences

def parse_transposed_table(table):
    sentences = []
    rows = table.rows
    
    # 1. Identify the "Category" (Cell 0,0)
    # Example: "Ngũ hành"
    category_name = rows[0].cells[0].text.strip()
    
    # 2. Identify the Entities (Row 0, starting from Col 1)
    # Example: ["Mộc", "Hỏa", "Thổ", "Kim", "Thủy"]
    entities = [c.text.strip() for c in rows[0].cells] 
    
    # 3. Iterate through the Attribute Rows (Row 1 onwards)
    for r in range(1, len(rows)):
        # Identify the Attribute Name (Col 0)
        # Example: "Ngũ cầm"
        attribute_name = rows[r].cells[0].text.strip()
        
        # Iterate through the columns to match Attribute with Entity
        for c in range(1, len(entities)):
            entity_name = entities[c]
            value = rows[r].cells[c].text.strip()
            
            # Skip empty cells
            if not value: continue
            
            # --- THE TARGET FORMAT ---
            # Template: "Với [Category] là [Entity], [Attribute] là [Value]."
            # Example: "Với Ngũ hành là Mộc, Ngũ cầm là Lộc."
            sent = f"Với {category_name} là {entity_name}, {attribute_name} là {value}."
            sentences.append(sent)

            
    return sentences

def parse_grouped_header_table(table):
    sentences = []
    
    # 1. Get the Main Subject Category (Row 0, Col 0)
    # Example: "Ngũ hành"
    subject_header = table.rows[0].cells[0].text.strip()
    
    # 2. Map distinct columns to their (Parent, Child) headers
    # We iterate column by column to handle the merging correctly
    col_mappings = []
    
    # Determine number of columns based on Row 1 (which usually has the most individual cells)
    num_cols = len(table.rows[1].cells)
    
    for j in range(1, num_cols):
        # Parent Header is in Row 0 (e.g., "Tự nhiên")
        # In python-docx, merged cells typically return the text of the top-left cell, 
        # so table.rows[0].cells[j] will correctly give "Tự nhiên" for all columns under it.
        parent_header = table.rows[0].cells[j].text.strip()
        
        # Child Header is in Row 1 (e.g., "Hướng", "Mùa")
        child_header = table.rows[1].cells[j].text.strip()
        
        col_mappings.append({
            "col_idx": j,
            "parent": parent_header,
            "child": child_header
        })
        
    # 3. Iterate through Data Rows (Row 2 onwards)
    for row in table.rows[2:]:
        # Subject is Col 0 (e.g., "Mộc", "Hỏa")
        subject = row.cells[0].text.strip()
        
        for mapping in col_mappings:
            col_idx = mapping["col_idx"]
            
            # Safety check: ensure row has this column
            if col_idx < len(row.cells):
                value = row.cells[col_idx].text.strip()
                
                # Skip empty values
                if not value: 
                    continue

                # --- THE FORMAT YOU REQUESTED ---
                # Template: "với [Subject] là [Subject_Header], [Child] trong [Parent] là [Value]"
                # Example: "với Mộc là Ngũ hành, Hướng trong Tự nhiên là Đông"
                
                # Handle case where Parent might be empty (just in case)
                if mapping["parent"]:
                    sent = (f"Với {subject} là {subject_header}, "
                            f"{mapping['child']} trong {mapping['parent']} là {value}.")
                else:
                    # Fallback if no parent group exists
                    sent = (f"Với {subject} là {subject_header}, "
                            f"{mapping['child']} là {value}.")
                            
                sentences.append(sent)

    return sentences

def parse_headless_table(table, context):
    # No Header: Inject context
    sentences = []
    for row in table.rows:
        entity = row.cells[0].text.strip()
        value = row.cells[1].text.strip()
        # Force a generic relation based on context
        sentences.append(f"Trong {context}, {entity} diễn ra vào thời gian {value}.")

    return sentences

