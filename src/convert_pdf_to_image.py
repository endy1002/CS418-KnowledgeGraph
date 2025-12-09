import pymupdf
import os

def convert_pdf_to_image(pdf_path, output_folder, image_format='png', dpi=300):
    """
    Convert each page of a PDF file to an image and save them in the specified output folder.

    :param pdf_path: Path to the input PDF file.
    :param output_folder: Folder where the output images will be saved.
    :param image_format: Format of the output images (default is 'png').
    :param dpi: Resolution of the output images (default is 300).
    """
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Open the PDF file
    pdf_document = pymupdf.open(pdf_path)

    # Iterate through each page in the PDF
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        
        # Render the page to an image
        zoom = dpi / 72  # 72 is the default DPI
        mat = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Construct the output image path
        image_path = os.path.join(output_folder, f'page_{page_number + 1}.{image_format}')

        # Save the image
        pix.save(image_path)

    print(f"Converted {len(pdf_document)} pages to images in '{output_folder}'.")


path = os.path.dirname(os.path.abspath(__file__))
current_folder = os.path.abspath(os.path.join(path, os.pardir))
for filename in os.listdir(current_folder):
    if filename.endswith(".pdf"):
        name = os.path.splitext(filename)[0]
        # Build a stable output path relative to this script's location
        pdf_file_path = os.path.abspath(os.path.join(path, "..", "assets", "data", name))
        os.makedirs(pdf_file_path, exist_ok=True)
        convert_pdf_to_image(os.path.join(current_folder, filename), pdf_file_path)
