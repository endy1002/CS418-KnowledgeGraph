import os
from pathlib import Path

def combine_spellfix_files(start_page, end_page, parent_dir_name, output_filename="combined_corpus.txt"):
    """
    Combines .spellfix.txt files from page folders within a specific directory structure.

    Args:
        start_page (int): The first page number (e.g., 31).
        end_page (int): The last page number (e.g., 71).
        parent_dir_name (str): The name of the parent folder (e.g., 'yduoctruyenthong').
        output_filename (str): The name of the final combined output file.
    """
    # 1. Define the base path relative to where this script is run
    # Assuming the structure is: ScriptLocation/../yduoctruyenthong/yduoctruyenthong/...
    
    # Go up one level (..), then into the target directory (yduoctruyenthong/yduoctruyenthong)
    base_path = Path.cwd() / parent_dir_name / parent_dir_name
    
    print(f"Starting directory search at: {base_path}")
    
    # Ensure the target directory exists
    if not base_path.exists():
        print(f"Error: Base directory not found at {base_path}")
        return

    # 2. Open the final output file for writing
    output_file_path = Path.cwd() / output_filename
    
    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        
        # 3. Iterate through the desired page range
        for page_num in range(start_page, end_page + 1):
            folder_name = f"page_{page_num}"
            
            # The expected file name is the folder name + ".spellfix.txt"
            file_name = f"{folder_name}.spellfix.txt"
            
            # Construct the full path to the input file
            input_file_path = base_path / folder_name / file_name

            if input_file_path.exists():
                print(f"Processing {input_file_path.name}...")
                
                try:
                    # 4. Read the content of the spellfix file
                    content = input_file_path.read_text(encoding='utf-8')
                    
                    # 5. Write the content to the output file
                    # Add a header to indicate the source of the content (useful for debugging/tracking)
                    outfile.write(f"\n\n--- START OF PAGE {page_num} ---\n\n")
                    outfile.write(content)
                    
                except Exception as e:
                    print(f"Could not read file {input_file_path}: {e}")
            else:
                print(f"Warning: File not found for page {page_num} at {input_file_path}")

    print("\n--- COMBINATION COMPLETE ---")
    print(f"All files combined into: {output_file_path}")

# --- CONFIGURATION ---
combine_spellfix_files(
    start_page=126, 
    end_page=150, 
    parent_dir_name='yduoctruyenthong'
)